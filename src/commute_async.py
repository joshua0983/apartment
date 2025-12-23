"""
Async commute calculator using Google Maps Distance Matrix API
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import aiohttp
import os


class AsyncCommuteCalculator:
    """Calculate commute times to office locations using async HTTP"""
    
    # Office locations
    OFFICES = {
        'office_1': {
            'address': '110 E 59th St, New York, NY 10022',
            'name': 'Office 1 (Midtown East)'
        },
        'office_2': {
            'address': '767 5th Ave, New York, NY 10153',
            'name': 'Office 2 (Midtown)'
        },
        'office_3': {
            'address': '130 Prince St, New York, NY 10012',
            'name': 'Office 3 (SoHo)'
        },
        'office_4': {
            'address': '40 W 23rd St, New York, NY 10010',
            'name': 'Office 4 (Chelsea)'
        },
    }
    
    def __init__(self, api_key: str):
        """
        Initialize async commute calculator
        
        Args:
            api_key: Google Maps API key
        """
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        
    async def _fetch_distance_matrix(
        self, 
        session: aiohttp.ClientSession,
        origin: str,
        destination: str,
        arrival_time: datetime
    ) -> Dict:
        """
        Fetch distance matrix from Google Maps API
        
        Args:
            session: aiohttp client session
            origin: Origin coordinates as "lat,lng"
            destination: Destination address
            arrival_time: Target arrival time
            
        Returns:
            API response JSON
        """
        params = {
            'origins': origin,
            'destinations': destination,
            'mode': 'transit',
            'arrival_time': int(arrival_time.timestamp()),
            'units': 'imperial',
            'key': self.api_key
        }
        
        async with session.get(self.base_url, params=params) as response:
            return await response.json()
    
    async def calculate_commutes(
        self, 
        origin: Tuple[float, float],
        arrival_time: Optional[datetime] = None
    ) -> Dict[str, Dict]:
        """
        Calculate morning commute times to all offices in parallel
        
        Args:
            origin: (latitude, longitude) of apartment
            arrival_time: Target arrival time (default: tomorrow 9 AM)
            
        Returns:
            Dictionary with commute data for each office
        """
        if arrival_time is None:
            arrival_time = self._get_next_weekday_morning()
        
        origin_str = f"{origin[0]},{origin[1]}"
        
        # Create async tasks for all offices
        async with aiohttp.ClientSession() as session:
            tasks = []
            office_names = []
            
            for office_id, office_info in self.OFFICES.items():
                office_address = office_info['address']
                office_name = office_info['name']
                
                task = self._fetch_distance_matrix(
                    session, 
                    origin_str, 
                    office_address, 
                    arrival_time
                )
                tasks.append(task)
                office_names.append(office_name)
            
            # Execute all API calls in parallel
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        results = {}
        for office_name, response in zip(office_names, responses):
            if isinstance(response, Exception):
                print(f"  Error calculating commute to {office_name}: {response}")
                results[office_name] = {
                    'duration_minutes': None,
                    'distance_miles': None,
                    'mode': 'transit',
                    'meets_preference': False,
                    'error': str(response)
                }
                continue
            
            try:
                if response['status'] == 'OK' and response['rows'][0]['elements'][0]['status'] == 'OK':
                    element = response['rows'][0]['elements'][0]
                    
                    duration_seconds = element['duration']['value']
                    duration_minutes = round(duration_seconds / 60)
                    
                    distance_text = element['distance']['text']
                    distance_miles = float(distance_text.split()[0]) if 'mi' in distance_text else None
                    
                    commute_data = {
                        'duration_minutes': duration_minutes,
                        'duration_text': element['duration']['text'],
                        'distance_miles': distance_miles,
                        'distance_text': distance_text,
                        'mode': 'transit',
                        'meets_preference': duration_minutes < 30,
                    }
                else:
                    commute_data = {
                        'duration_minutes': None,
                        'distance_miles': None,
                        'mode': 'transit',
                        'meets_preference': False,
                        'error': 'Route not found'
                    }
                    
            except Exception as e:
                print(f"  Error parsing response for {office_name}: {e}")
                commute_data = {
                    'duration_minutes': None,
                    'distance_miles': None,
                    'mode': 'transit',
                    'meets_preference': False,
                    'error': str(e)
                }
            
            results[office_name] = commute_data
        
        return results
    
    def _get_next_weekday_morning(self) -> datetime:
        """Get next weekday at 9 AM for commute calculation"""
        now = datetime.now()
        next_day = now + timedelta(days=1)
        
        # If weekend, move to Monday
        while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
            next_day += timedelta(days=1)
        
        return next_day.replace(hour=9, minute=0, second=0, microsecond=0)
    
    def meets_commute_preference(self, commutes: Dict[str, Dict]) -> bool:
        """
        Check if at least one office has < 30 min commute
        
        Args:
            commutes: Dictionary of commute data
            
        Returns:
            True if any office is < 30 minutes
        """
        return any(
            c.get('duration_minutes', float('inf')) < 30 
            for c in commutes.values()
        )
