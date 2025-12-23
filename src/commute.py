"""
Commute calculator using Google Maps Distance Matrix API
"""

from typing import Dict, List, Optional, Tuple
import googlemaps
from datetime import datetime, timedelta
import os


class CommuteCalculator:
    """Calculate commute times to office locations"""
    
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
        Initialize commute calculator
        
        Args:
            api_key: Google Maps API key
        """
        self.client = googlemaps.Client(key=api_key)
        # Resolve office coordinates on init
        self.office_coords = self._resolve_office_coordinates()
        
    def _resolve_office_coordinates(self) -> Dict[str, str]:
        """Get office addresses for API calls"""
        resolved = {}
        
        for office_id, office_info in self.OFFICES.items():
            resolved[office_id] = office_info['address']
        
        return resolved
        
    def calculate_commutes(
        self, 
        origin: Tuple[float, float],
        arrival_time: Optional[datetime] = None
    ) -> Dict[str, Dict]:
        """
        Calculate morning commute times to all offices
        
        Args:
            origin: (latitude, longitude) of apartment
            arrival_time: Target arrival time (default: tomorrow 9 AM)
            
        Returns:
            Dictionary with commute data for each office
        """
        if arrival_time is None:
            # Default to next weekday at 9 AM
            arrival_time = self._get_next_weekday_morning()
        
        results = {}
        origin_str = f"{origin[0]},{origin[1]}"
        
        for office_id, office_location in self.office_coords.items():
            office_name = self.OFFICES[office_id]['name']
            
            try:
                if office_location is None:
                    results[office_name] = {
                        'duration_minutes': None,
                        'distance_miles': None,
                        'mode': 'transit',
                        'meets_preference': False,
                        'error': 'Office location not resolved'
                    }
                    continue
                
                # Call Distance Matrix API
                result = self.client.distance_matrix(
                    origins=[origin_str],
                    destinations=[office_location],
                    mode="transit",
                    arrival_time=arrival_time,
                    units="imperial"
                )
                
                if result['status'] == 'OK' and result['rows'][0]['elements'][0]['status'] == 'OK':
                    element = result['rows'][0]['elements'][0]
                    
                    duration_seconds = element['duration']['value']
                    duration_minutes = round(duration_seconds / 60)
                    
                    distance_text = element['distance']['text']
                    # Parse distance (e.g., "5.2 mi")
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
                print(f"  Error calculating commute to {office_name}: {e}")
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

