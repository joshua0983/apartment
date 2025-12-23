"""
Test script for address-based apartment evaluation
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import evaluate_address


def test_address(address: str):
    """Test evaluation for a specific address"""
    print(f"\n{'='*70}")
    print(f"Testing Address Evaluation")
    print(f"{'='*70}\n")
    
    try:
        result = evaluate_address(address)
        
        print("\n" + "="*70)
        print("EVALUATION COMPLETE")
        print("="*70)
        print(f"\nAddress: {result.get('address')}")
        print(f"Score: {result.get('score')}/5.00")
        
        print("\nCommute Times:")
        for office, data in result.get('commutes', {}).items():
            duration = data.get('duration_minutes', 'N/A')
            status = "✓" if data.get('meets_preference') else "✗"
            print(f"  {status} {office}: {duration} minutes")
        
        subway = result.get('subway', {})
        print(f"\nNearest Subway:")
        if subway.get('station_name'):
            status = "✓" if subway.get('meets_preference') else "✗"
            print(f"  {status} {subway['station_name']} ({', '.join(subway['lines'])})")
            print(f"     {subway['walk_time_minutes']} min walk ({subway['distance_miles']} mi)")
        else:
            print(f"  ✗ No nearby station found")
        
        amenities = result.get('amenities', {})
        print(f"\nAmenities (within {amenities.get('search_radius_miles', 0.5)} miles):")
        print(f"  Restaurants: {amenities.get('restaurants', 0)}")
        print(f"  Cafes: {amenities.get('cafes', 0)}")
        print(f"  Bars: {amenities.get('bars', 0)}")
        print(f"  Bubble Tea: {amenities.get('bubble_tea', 0)}")
        print(f"  Density Score: {amenities.get('amenity_density_score', 0)}/10")
        
        print(f"\n{result.get('explanation', '')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_address.py '<address>'")
        print("Example: python test_address.py '34-20 30th Street, Queens, NY 11101'")
        sys.exit(1)
    
    address = sys.argv[1]
    result = test_address(address)
    
    if result:
        print("\n✓ Test completed successfully")
    else:
        print("\n✗ Test failed")
        sys.exit(1)
