"""
Async version of main entry point for apartment address evaluator
"""

import os
import json
from typing import Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv
import aiohttp

from src.commute_async import AsyncCommuteCalculator
from src.proximity_async import AsyncProximityAnalyzer
from src.scorer import ApartmentScorer


async def geocode_address_async(address: str, api_key: str) -> Dict:
    """
    Geocode address using Google Maps Geocoding API (async)
    
    Args:
        address: Full street address
        api_key: Google Maps API key
        
    Returns:
        Dictionary with coordinates and formatted address
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': api_key
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            result = await response.json()
    
    if not result.get('results'):
        return {
            'error': 'Address not found',
            'formatted_address': None,
            'latitude': None,
            'longitude': None
        }
    
    location = result['results'][0]['geometry']['location']
    return {
        'formatted_address': result['results'][0]['formatted_address'],
        'latitude': location['lat'],
        'longitude': location['lng']
    }


async def evaluate_address_async(
    address: str, 
    custom_offices: Optional[List[Dict]] = None,
    verbose: bool = True
) -> Dict:
    """
    Evaluate an apartment address asynchronously
    
    Args:
        address: Full street address (e.g., "123 Main St, Queens, NY 11101")
        custom_offices: Optional list of custom office locations
        verbose: Whether to print progress messages
        
    Returns:
        Dictionary with evaluation results
    """
    # Load environment variables
    load_dotenv()
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if not google_api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not found in environment")
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Evaluating Address: {address}")
        print(f"{'='*60}\n")
    
    # Step 1: Geocode address to get coordinates
    if verbose:
        print("Step 1: Geocoding address...")
    
    try:
        geocode_result = await geocode_address_async(address, google_api_key)
        
        if 'error' in geocode_result:
            if verbose:
                print(f"❌ Could not find address: {address}")
            return {
                'address': address,
                'timestamp': datetime.now().isoformat(),
                'error': geocode_result['error'],
                'score': 0.0,
            }
        
        latitude = geocode_result['latitude']
        longitude = geocode_result['longitude']
        formatted_address = geocode_result['formatted_address']
        
        if verbose:
            print(f"✓ Found: {formatted_address}")
            print(f"  Coordinates: ({latitude}, {longitude})")
        
    except Exception as e:
        if verbose:
            print(f"❌ Error geocoding address: {e}")
        return {
            'address': address,
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'score': 0.0,
        }
    
    location_coords = (latitude, longitude)
    
    # Initialize calculators
    commute_calc = AsyncCommuteCalculator(google_api_key)
    proximity = AsyncProximityAnalyzer(google_api_key)
    
    # Steps 2-4: Run commute, subway, and amenities in parallel
    if verbose:
        print("\nStep 2-4: Calculating commutes, subway, and amenities in parallel...")
    
    import asyncio
    
    # Execute all async operations concurrently
    commutes_task = commute_calc.calculate_commutes(location_coords)
    amenities_task = proximity.find_activity_areas(location_coords)
    
    # Subway is synchronous (uses local data)
    subway_data = proximity.find_nearest_subway(location_coords)
    
    # Wait for async tasks
    commutes, amenities_data = await asyncio.gather(commutes_task, amenities_task)
    
    if verbose:
        # Print commute results
        print("\n  Commute times:")
        for office, data in commutes.items():
            duration = data.get('duration_minutes')
            if duration:
                print(f"    {office}: {duration} minutes")
            else:
                print(f"    {office}: Unable to calculate")
        
        # Print subway result
        if subway_data.get('station_name'):
            print(f"\n  Nearest subway: {subway_data['station_name']} "
                  f"({subway_data.get('walk_time_minutes', 'N/A')} min walk)")
        else:
            print(f"\n  Unable to find nearby subway station")
        
        # Print amenities result
        if amenities_data.get('total_amenities') is not None:
            print(f"\n  Amenities: {amenities_data['total_amenities']} within walking distance")
            print(f"  Density score: {amenities_data.get('amenity_density_score', 0):.1f}/10")
        else:
            print(f"\n  Unable to analyze amenities")
    
    # Step 5: Calculate score
    if verbose:
        print("\nStep 5: Calculating final score...")
    
    scorer = ApartmentScorer()
    result = scorer.calculate_score(
        meets_requirements=True,  # No hard requirements for address-only evaluation
        commutes=commutes,
        subway_data=subway_data,
        amenities_data=amenities_data
    )
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"FINAL SCORE: {result['score']}/5.00")
        print(f"{'='*60}")
        print(f"{result['explanation']}\n")
    
    # Compile full result
    full_result = {
        'address': formatted_address,
        'input_address': address,
        'timestamp': datetime.now().isoformat(),
        'coordinates': {'latitude': latitude, 'longitude': longitude},
        'commutes': commutes,
        'subway': subway_data,
        'amenities': amenities_data,
        'score': result['score'],
        'breakdown': result['breakdown'],
        'explanation': result['explanation'],
    }
    
    return full_result


def save_result(result: Dict, output_dir: str = '../output'):
    """Save evaluation result to JSON file"""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"evaluation_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to: {filepath}")


if __name__ == '__main__':
    import asyncio
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python main_async.py <address>")
        sys.exit(1)
    
    address = sys.argv[1]
    
    # Run async evaluation
    result = asyncio.run(evaluate_address_async(address))
    
    # Save result
    save_result(result)
