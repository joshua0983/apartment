"""
Calculate proximity to subway stations and activity areas
"""

from typing import Dict, List, Optional, Tuple
from geopy.distance import geodesic
import googlemaps
import json
import os


class ProximityAnalyzer:
    """Analyze proximity to transit and amenities"""
    
    def __init__(self, google_api_key: Optional[str] = None):
        """
        Initialize proximity analyzer
        
        Args:
            google_api_key: Google Maps API key for Places API
        """
        self.google_api_key = google_api_key
        if google_api_key:
            self.gmaps = googlemaps.Client(key=google_api_key)
        else:
            self.gmaps = None
        
        # Load subway station data
        self.subway_stations = self._load_subway_stations()
        
    def _load_subway_stations(self) -> List[Dict]:
        """Load NYC subway station data from JSON file"""
        # Try multiple possible paths
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
            except Exception as e:
                continue
        
        print("Warning: Could not load subway station data. Using empty list.")
        return []
        
    def find_nearest_subway(self, location: Tuple[float, float]) -> Dict:
        """
        Find nearest NYC subway station
        
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
                'meets_preference': walk_time < 5,  # < 5 minutes preferred
            }
        
        return {
            'station_name': None,
            'distance_miles': None,
            'walk_time_minutes': None,
            'lines': [],
            'meets_preference': False,
        }
    
    def find_activity_areas(self, location: Tuple[float, float], radius_miles: float = 0.5) -> Dict:
        """
        Find proximity to commercial/activity areas using Google Places API
        
        Args:
            location: (latitude, longitude) of apartment
            radius_miles: Search radius in miles (default: 0.5 mile walking distance)
            
        Returns:
            Dictionary with activity area analysis
        """
        if not self.gmaps:
            return {
                'total_amenities': None,
                'restaurants': 0,
                'cafes': 0,
                'bars': 0,
                'amenity_density_score': 0.0,
                'error': 'Google Maps API not available'
            }
        
        # Convert miles to meters (Google Places API uses meters)
        radius_meters = int(radius_miles * 1609.34)
        
        amenity_counts = {
            'restaurants': 0,
            'cafes': 0,
            'bars': 0,
            'bubble_tea': 0,
        }
        
        # Search for different types of amenities
        search_types = {
            'restaurants': 'restaurant',
            'cafes': 'cafe',
            'bars': 'bar',
        }
        
        try:
            for category, place_type in search_types.items():
                result = self.gmaps.places_nearby(
                    location=location,
                    radius=radius_meters,
                    type=place_type
                )
                
                if result['status'] == 'OK':
                    amenity_counts[category] = len(result.get('results', []))
            
            # Search for bubble tea specifically
            bubble_tea_result = self.gmaps.places_nearby(
                location=location,
                radius=radius_meters,
                keyword='bubble tea'
            )
            
            if bubble_tea_result['status'] == 'OK':
                amenity_counts['bubble_tea'] = len(bubble_tea_result.get('results', []))
            
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
