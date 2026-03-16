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
        self.directions_url = "https://maps.googleapis.com/maps/api/directions/json"
        
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
        Legacy synchronous nearest subway calculation using geodesic distance.
        Kept for backwards compatibility; new async code should use
        find_nearest_subway_async which leverages Google Directions for
        walking time.
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

    async def _get_walking_time_via_directions(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
    ) -> Optional[float]:
        """
        Get walking time in minutes between origin and destination using
        Google Directions API. Returns None on error.
        """
        if not self.google_api_key:
            return None

        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": "walking",
            "key": self.google_api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.directions_url, params=params) as resp:
                    data = await resp.json()

            if data.get("status") != "OK":
                print(f"  Directions API error: {data.get('status')}, {data.get('error_message')}")
                return None

            route = data["routes"][0]
            leg = route["legs"][0]
            seconds = leg["duration"]["value"]
            return seconds / 60.0

        except Exception as e:
            print(f"  Error calling Directions API: {e}")
            return None

    async def find_nearest_subway_async(self, location: Tuple[float, float]) -> Dict:
        """
        Find nearest NYC subway station and walking time using Google Directions.
        Falls back to geodesic-based estimate if Directions API fails.
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

        nearest_station = None
        min_distance = float('inf')

        for station in self.subway_stations:
            station_coords = (station['latitude'], station['longitude'])
            distance = geodesic(location, station_coords).miles

            if distance < min_distance:
                min_distance = distance
                nearest_station = station

        if not nearest_station:
            return {
                'station_name': None,
                'distance_miles': None,
                'walk_time_minutes': None,
                'lines': [],
                'meets_preference': False,
            }

        station_coords = (nearest_station['latitude'], nearest_station['longitude'])

        walk_time = await self._get_walking_time_via_directions(location, station_coords)

        if walk_time is None:
            walk_time = self._calculate_walk_time(min_distance)

        return {
            'station_name': nearest_station['name'],
            'distance_miles': round(min_distance, 2),
            'walk_time_minutes': round(walk_time),
            'lines': nearest_station['lines'],
            'meets_preference': walk_time < 5,
        }
    
    async def _fetch_places_nearby(
        self,
        session: aiohttp.ClientSession,
        location: Tuple[float, float],
        radius_meters: int,
        place_type: Optional[str] = None,
        keyword: Optional[str] = None,
        max_results: int = 20,
        max_pages: int = 1,
    ) -> Dict:
        """
        Fetch nearby places from Google Places API, following pagination.
        
        Args:
            session: aiohttp client session
            location: (latitude, longitude) to search around
            radius_meters: Search radius in meters
            place_type: Type of place to search for (e.g., 'restaurant')
            keyword: Keyword to search for (e.g., 'bubble tea')
            max_results: Max results to aggregate per category (default: 20)
            max_pages: Max paginated responses to fetch (default: 1, i.e. single page)
            
        Returns:
            Dictionary in the same shape as a single Places API response,
            but with `results` aggregated across pages.
        """
        if not self.google_api_key:
            return {"status": "NO_API_KEY", "results": []}

        aggregated_results: List[Dict] = []
        next_page_token: Optional[str] = None
        pages_fetched = 0
        last_status: Optional[str] = None

        while pages_fetched < max_pages and len(aggregated_results) < max_results:
            params: Dict[str, object] = {
                "key": self.google_api_key,
            }

            if next_page_token:
                params["pagetoken"] = next_page_token
            else:
                params.update(
                    {
                        "location": f"{location[0]},{location[1]}",
                        "radius": radius_meters,
                    }
                )
                if place_type:
                    params["type"] = place_type
                if keyword:
                    params["keyword"] = keyword

            async with session.get(self.places_url, params=params) as response:
                data = await response.json()

            status = data.get("status")
            last_status = status

            if status != "OK":
                # ZERO_RESULTS just means nothing found; anything else we log and stop.
                if status not in ("ZERO_RESULTS", "OK"):
                    print(f"  Places API error ({place_type or keyword}): {status} {data.get('error_message')}")
                break

            page_results = data.get("results", [])
            aggregated_results.extend(page_results)

            next_page_token = data.get("next_page_token")
            pages_fetched += 1

            if not next_page_token or len(aggregated_results) >= max_results:
                break

            # Google docs require a short delay before using next_page_token
            await asyncio.sleep(2.0)

        # Truncate to max_results in case we went slightly over
        aggregated_results = aggregated_results[:max_results]

        return {
            "status": last_status or "ZERO_RESULTS",
            "results": aggregated_results,
        }
    
    async def find_activity_areas(self, location: Tuple[float, float], max_walk_minutes: float =20.0) -> Dict:
        """
        Find proximity to commercial/activity areas using Google Places API (async)
        
        Args:
            location: (latitude, longitude) of apartment
            max_walk_minutes: Walking time budget in minutes (default: 10 minutes)
            
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
        
        # Convert walking time budget to distance radius in meters
        WALKING_SPEED_MPH = 3.0
        radius_miles = (WALKING_SPEED_MPH * max_walk_minutes) / 60.0
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
                    results = response.get('results', [])

                    # For bubble tea, be stricter but still practical:
                    # only count places that look like actual bubble tea
                    # / tea shops (not wholesale supply stores).
                    if category == 'bubble_tea':
                        filtered = []
                        for place in results:
                            name = (place.get('name') or '').lower()
                            types_list = place.get('types') or []
                            types_str = ' '.join(types_list).lower()
                            
                            # Basic name-based signals that this is a tea/boba shop
                            name_has_bubble_tea = any(
                                kw in name
                                for kw in [
                                    'bubble tea',
                                    'bubble-tea',
                                    'bubbletea',
                                    'boba',
                                    'milk tea',
                                    'tea house',
                                    'teahouse',
                                ]
                            )

                            # Tea/cafe/food related place types
                            has_food_type = any(
                                t in types_str
                                for t in [
                                    'cafe',
                                    'restaurant',
                                    'food',
                                    'bakery',
                                ]
                            )

                            # Exclude obvious supply / equipment / training-only places
                            looks_like_supply = any(
                                bad in name
                                for bad in [
                                    'supplies',
                                    'wholesale',
                                    'equipment',
                                    'training',
                                ]
                            ) and 'store' in types_str and 'food' not in types_str

                            if (name_has_bubble_tea or ('tea' in name and has_food_type)) and not looks_like_supply:
                                filtered.append(place)
                        results = filtered

                        # Debug logging to inspect which bubble tea places
                        # are being counted within the current walk radius.
                        print(f"Bubble tea places within ~{max_walk_minutes} min radius (count={len(results)}):")
                        for p in results:
                            print("  -", p.get('name'), "| types:", p.get('types'))

                    amenity_counts[category] = len(results)
            
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
            'max_walk_minutes': max_walk_minutes,
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
