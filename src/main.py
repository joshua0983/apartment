"""
Main entry point for apartment address evaluator
"""

import os
import json
from typing import Dict
from datetime import datetime
from dotenv import load_dotenv
import googlemaps

from commute import CommuteCalculator
from proximity import ProximityAnalyzer
from scorer import ApartmentScorer


def evaluate_address(address: str) -> Dict:
    """
    Evaluate an apartment address
    
    Args:
        address: Full street address (e.g., "123 Main St, Queens, NY 11101")
        
    Returns:
        Dictionary with evaluation results
    """
    # Load environment variables
    load_dotenv()
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if not google_api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not found in environment")
    
    print(f"\n{'='*60}")
    print(f"Evaluating Address: {address}")
    print(f"{'='*60}\n")
    
    # Step 1: Geocode address to get coordinates
    print("Step 1: Geocoding address...")
    try:
        gmaps = googlemaps.Client(key=google_api_key)
        geocode_result = gmaps.geocode(address)
        
        if not geocode_result:
            print(f"❌ Could not find address: {address}")
            return {
                'address': address,
                'timestamp': datetime.now().isoformat(),
                'error': 'Address not found',
                'score': 0.0,
            }
        
        location = geocode_result[0]['geometry']['location']
        latitude = location['lat']
        longitude = location['lng']
        formatted_address = geocode_result[0]['formatted_address']
        
        print(f"✓ Found: {formatted_address}")
        print(f"  Coordinates: ({latitude}, {longitude})")
        
    except Exception as e:
        print(f"❌ Error geocoding address: {e}")
        return {
            'address': address,
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'score': 0.0,
        }
    
    location_coords = (latitude, longitude)
    
    # Step 2: Calculate commutes
    print("\nStep 2: Calculating commute times...")
    commute_calc = CommuteCalculator(google_api_key)
    commutes = commute_calc.calculate_commutes(location_coords)
    
    for office, data in commutes.items():
        duration = data.get('duration_minutes')
        if duration:
            print(f"  {office}: {duration} minutes")
        else:
            print(f"  {office}: Unable to calculate")
    
    # Step 3: Find nearest subway
    print("\nStep 3: Finding nearest subway station...")
    proximity = ProximityAnalyzer(google_api_key)
    subway_data = proximity.find_nearest_subway(location_coords)
    
    if subway_data.get('station_name'):
        print(f"  Nearest: {subway_data['station_name']} "
              f"({subway_data.get('walk_time_minutes', 'N/A')} min walk)")
    else:
        print(f"  Unable to find nearby subway station")
    
    # Step 4: Analyze amenities
    print("\nStep 4: Analyzing nearby amenities...")
    amenities_data = proximity.find_activity_areas(location_coords)
    
    if amenities_data.get('total_amenities') is not None:
        print(f"  Found {amenities_data['total_amenities']} amenities within walking distance")
        print(f"  Density score: {amenities_data.get('amenity_density_score', 0):.1f}/10")
    else:
        print(f"  Unable to analyze amenities")
    
    # Step 5: Calculate score
    print("\nStep 5: Calculating final score...")
    scorer = ApartmentScorer()
    result = scorer.calculate_score(
        meets_requirements=True,  # No hard requirements for address-only evaluation
        commutes=commutes,
        subway_data=subway_data,
        amenities_data=amenities_data
    )
    
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
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <address>")
        print("Example: python main.py '123 Main St, Queens, NY 11101'")
        sys.exit(1)
    
    address = sys.argv[1]
    
    try:
        result = evaluate_address(address)
        save_result(result)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
