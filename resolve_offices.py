"""
Helper script to resolve Google Maps share URLs to full addresses
"""

import sys
import os
from dotenv import load_dotenv
import googlemaps
import requests

load_dotenv()
api_key = os.getenv('GOOGLE_MAPS_API_KEY')

if not api_key:
    print("Error: GOOGLE_MAPS_API_KEY not found in .env")
    sys.exit(1)

gmaps = googlemaps.Client(key=api_key)

# Office URLs from commute.py
urls = [
    'https://maps.app.goo.gl/smkZJp2qrVeis9L89',
    'https://maps.app.goo.gl/AWLA9pQ7VHrcjZzU9',
    'https://maps.app.goo.gl/4yS8EqFvCW45pamp7',
]

print("Resolving Google Maps URLs...\n")
print("Copy these addresses to src/commute.py:\n")

for i, url in enumerate(urls, 1):
    try:
        # Follow redirect to get full URL
        response = requests.get(url, allow_redirects=True)
        full_url = response.url
        
        # Try to extract place name or coordinates from URL
        if 'place/' in full_url:
            place_name = full_url.split('place/')[1].split('/')[0].replace('+', ' ')
            print(f"Office {i}: '{place_name}'")
        elif '@' in full_url:
            # Extract coordinates
            coords_part = full_url.split('@')[1].split(',')[:2]
            lat, lon = coords_part[0], coords_part[1]
            # Reverse geocode
            result = gmaps.reverse_geocode((float(lat), float(lon)))
            if result:
                address = result[0]['formatted_address']
                print(f"Office {i}: '{address}'")
            else:
                print(f"Office {i}: Coordinates ({lat}, {lon})")
        else:
            print(f"Office {i}: Could not parse - {full_url}")
            
    except Exception as e:
        print(f"Office {i}: Error - {e}")

print("\n" + "="*60)
print("Update src/commute.py OFFICES dict with these addresses:")
print("Replace 'url' field with 'address' field for each office")
