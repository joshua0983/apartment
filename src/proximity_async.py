"""
Async proximity analyzer for subway stations and amenities
"""

from typing import Dict, List, Optional, Tuple
from geopy.distance import geodesic
import asyncio
import aiohttp
import json
import os


class AsyncProximityAnalyzer:
    """Analyze proximity to transit and amenities using async HTTP"""
    
    def __init__(self, google_api_key: Optional[str] = None):
        """
        Initialize async proximity analyzer
        
        Args:
            google_api_key: Google Maps API key for Places API
        """
        self.google_api_key = google_api_key
        self.places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        # Load subway station data
        self.subway_stations = self._load_subway_stations()
        
    def _load_subway_stations(self) -> List[Dict]:
        """Load NYC subway station data from JSON file"""
        possible_paths = [
            '../data/subway_stations.json',
            'data/subway_stations.json',
            os.path.join(os.path.dirname(__file__), '../data/subway_stations.json'),
        ]
        
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return json.load(f)
            except Exception:
                continue
        
        print("Warning: Could not load subway station data. Using empty list.")
        return []
        
    def find_nearest_subway(self, location: Tuple[float, float]) -> Dict:
        """
        Find nearest NYC subway station (synchronous - uses local data)
        
        Args:
            location: (latitude, longitude) of apartment
            
        Returns:
            Dictionary with nearest station info
        """
        if not self.subway_stations:
            return {
                'station_name': None,
                'distance_miles': None,
                'walk_time_minutes': None,
                'lines': [],
                'meets_preference': False,
                'error': 'Subway data not available'
            }
        
        # Calculate distance to all stations
        nearest_station = None
        min_distance = float('inf')
        
        for station in self.subway_stations:
            station_coords = (station['latitude'], station['longitude'])
            distance = geodesic(location, station_coords).miles
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        if nearest_station:
            walk_time = self._calculate_walk_time(min_distance)
            
            return {
                'station_name': nearest_station['name'],
                'distance_miles': round(min_distance, 2),
                'walk_time_minutes': round(walk_time),
                'lines': nearest_station['lines'],
                'meets_preference': walk_time < 5,
            }
        
        return {
            'station_name': None,
            'distance_miles': None,
            'walk_time_minutes': None,
            'lines': [],
            'meets_preference': False,
        }
    
    async def _fetch_places_nearby(
        self,
        session: aiohttp.ClientSession,
        location: Tuple[float, float],
        radius_meters: int,
        place_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict:
        """
        Fetch nearby places from Google Places API
        
        Args:
            session: aiohttp client session
            location: (latitude, longitude) to search around
            radius_meters: Search radius in meters
            place_type: Type of place to search for (e.g., 'restaurant')
            keyword: Keyword to search for (e.g., 'bubble tea')
            
        Returns:
            API response JSON
        """
        params = {
            'location': f"{location[0]},{location[1]}",
            'radius': radius_meters,
            'key': self.google_api_key
        }
        
        if place_type:
            params['type'] = place_type
        if keyword:
            params['keyword'] = keyword
        
        async with session.get(self.places_url, params=params) as response:
            return await response.json()
    
    async def find_activity_areas(self, location: Tuple[float, float], radius_miles: float = 0.5) -> Dict:
        """
        Find proximity to commercial/activity areas using Google Places API (async)
        
        Args:
            location: (latitude, longitude) of apartment
            radius_miles: Search radius in miles (default: 0.5 mile walking distance)
            
        Returns:
            Dictionary with activity area analysis
        """
        if not self.google_api_key:
            return {
                'total_amenities': None,
                'restaurants': 0,
                'cafes': 0,
                'bars': 0,
                'bubble_tea': 0,
                'amenity_density_score': 0.0,
                'error': 'Google Maps API not available'
            }
        
        # Convert miles to meters
        radius_meters = int(radius_miles * 1609.34)
        
        amenity_counts = {
            'restaurants': 0,
            'cafes': 0,
            'bars': 0,
            'bubble_tea': 0,
        }
        
        # Define search tasks
        search_configs = [
            {'place_type': 'restaurant', 'category': 'restaurants'},
            {'place_type': 'cafe', 'category': 'cafes'},
            {'place_type': 'bar', 'category': 'bars'},
            {'keyword': 'bubble tea', 'category': 'bubble_tea'},
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                categories = []
                
                for config in search_configs:
                    task = self._fetch_places_nearby(
                        session,
                        location,
                        radius_meters,
                        place_type=config.get('place_type'),
                        keyword=config.get('keyword')
                    )
                    tasks.append(task)
                    categories.append(config['category'])
                
                # Execute all API calls in parallel
                responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for category, response in zip(categories, responses):
                if isinstance(response, Exception):
                    print(f"  Error searching for {category}: {response}")
                    continue
                
                if response.get('status') == 'OK':
                    amenity_counts[category] = len(response.get('results', []))
            
        except Exception as e:
            print(f"  Error searching for amenities: {e}")
            return {
                'total_amenities': None,
                'restaurants': 0,
                'cafes': 0,
                'bars': 0,
                'bubble_tea': 0,
                'amenity_density_score': 0.0,
                'error': str(e)
            }
        
        # Calculate total and density score
        total_amenities = sum(amenity_counts.values())
        
        # Density score: 0-10 scale based on total amenities
        # 50+ amenities = 10, 0 amenities = 0
        density_score = min(10.0, (total_amenities / 50.0) * 10.0)
        
        return {
            'total_amenities': total_amenities,
            'restaurants': amenity_counts['restaurants'],
            'cafes': amenity_counts['cafes'],
            'bars': amenity_counts['bars'],
            'bubble_tea': amenity_counts['bubble_tea'],
            'amenity_density_score': round(density_score, 1),
            'search_radius_miles': radius_miles,
        }
    
    def _calculate_walk_time(self, distance_miles: float) -> float:
        """
        Estimate walk time in minutes
        
        Args:
            distance_miles: Distance in miles
            
        Returns:
            Estimated walk time in minutes (assuming 3 mph)
        """
        WALKING_SPEED_MPH = 3.0
        return (distance_miles / WALKING_SPEED_MPH) * 60
