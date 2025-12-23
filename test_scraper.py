"""
Test script for StreetEasy scraper
Run this to test the scraper with a real listing URL
"""

import sys
sys.path.insert(0, 'src')

from scraper import StreetEasyScraper
import json


def test_scraper(url: str, use_selenium: bool = False):
    """Test the scraper with a given URL"""
    print(f"\n{'='*70}")
    print(f"Testing StreetEasy Scraper")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"Method: {'Playwright + Stealth' if not use_selenium else 'Legacy Selenium'}")
    print(f"{'='*70}\n")
    
    # Create scraper with context manager for proper cleanup
    with StreetEasyScraper(use_playwright=not use_selenium) as scraper:
        # Scrape listing
        print("Scraping listing...")
        listing = scraper.scrape_listing(url)
        
        # Display results
        print("\n" + "="*70)
        print("LISTING DATA:")
        print("="*70)
        print(json.dumps(listing, indent=2))
        
        # Validate requirements
        print("\n" + "="*70)
        print("REQUIREMENTS VALIDATION:")
        print("="*70)
        meets_requirements, failed = scraper.validate_requirements(listing)
    
    if meets_requirements:
        print("✅ ALL REQUIREMENTS MET!")
    else:
        print("❌ FAILED REQUIREMENTS:")
        for fail in failed:
            print(f"   - {fail}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY:")
    print("="*70)
    print(f"Address: {listing.get('address', 'N/A')}")
    print(f"Bedrooms: {listing.get('bedrooms', 'N/A')}")
    print(f"Bathrooms: {listing.get('bathrooms', 'N/A')}")
    print(f"Price: ${listing.get('price', 'N/A'):,}" if listing.get('price') else "Price: N/A")
    print(f"Laundry: {listing.get('laundry', 'N/A')}")
    print(f"Cats Allowed: {listing.get('cats_allowed', 'N/A')}")
    print(f"Coordinates: {listing.get('latitude', 'N/A')}, {listing.get('longitude', 'N/A')}")
    print("="*70 + "\n")
    
    return listing, meets_requirements


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_scraper.py <streeteasy_url> [--selenium]")
        print("\nExample:")
        print("  python test_scraper.py 'https://streeteasy.com/building/...'")
        print("  python test_scraper.py 'https://streeteasy.com/rental/...' --selenium")
        sys.exit(1)
    
    url = sys.argv[1]
    use_selenium = '--selenium' in sys.argv or '-s' in sys.argv
    
    try:
        listing, valid = test_scraper(url, use_selenium)
        sys.exit(0 if valid else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
