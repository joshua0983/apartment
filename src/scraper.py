"""
StreetEasy listing scraper module
Extracts apartment details from StreetEasy URLs
"""

from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page
from playwright_stealth import stealth_sync
import re
import json
import time
import random


class StreetEasyScraper:
    """Scrapes apartment listing data from StreetEasy"""
    
    def __init__(self, use_playwright: bool = True):
        """
        Initialize scraper
        
        Args:
            use_playwright: Use Playwright for JavaScript-heavy pages (recommended)
        """
        self.use_playwright = use_playwright
        self.playwright = None
        self.browser = None
        self.context = None
        
        # Initialize browser if using Playwright
        if self.use_playwright:
            self._init_browser()
    
    def _init_browser(self):
        """Initialize Playwright browser (reusable across multiple listings)"""
        try:
            from playwright.sync_api import sync_playwright
            
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            print("Browser initialized successfully")
        except Exception as e:
            print(f"Failed to initialize browser: {e}")
            self.use_playwright = False
    
    def close(self):
        """Close browser and cleanup resources"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("Browser closed")
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()
        
    def scrape_listing(self, url: str) -> Dict:
        """
        Scrape apartment listing details
        
        Args:
            url: StreetEasy listing URL
            
        Returns:
            Dictionary with listing details
        """
        if self.use_playwright:
            return self._scrape_with_playwright(url)
        else:
            return self._scrape_with_requests(url)
    
    def _scrape_with_playwright(self, url: str) -> Dict:
        """Scrape using Playwright with stealth mode"""
        try:
            if not self.browser or not self.context:
                print("Browser not initialized, reinitializing...")
                self._init_browser()
            
            if not self.browser:
                print("Failed to initialize browser, falling back to requests")
                return self._scrape_with_requests(url)
            
            page = self.context.new_page()
            
            # Apply stealth mode
            stealth_sync(page)
            
            print(f"Loading page: {url}")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Random delay to mimic human behavior
            time.sleep(random.uniform(2, 4))
            
            # Get page content
            html_content = page.content()
            
            # Close the page (but keep browser open)
            page.close()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Debug: Print snippet
            page_snippet = soup.get_text()[:300]
            print(f"DEBUG - Page loaded successfully. Sample: {page_snippet[:150]}...")
            
            return self._parse_listing_data(soup, url)
                
        except Exception as e:
            print(f"Error scraping with Playwright: {e}")
            import traceback
            traceback.print_exc()
            print("Falling back to requests...")
            return self._scrape_with_requests(url)
    
    def _scrape_with_requests(self, url: str) -> Dict:
        """Scrape using requests + BeautifulSoup"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return self._parse_listing_data(soup, url)
            
        except Exception as e:
            print(f"Error scraping with requests: {e}")
            return self._get_empty_listing_data(url)
    
    def _parse_listing_data(self, soup: BeautifulSoup, url: str) -> Dict:
        """Parse listing data from BeautifulSoup object"""
        listing_data = self._get_empty_listing_data(url)
        
        # Try to extract from __NEXT_DATA__ JSON first (more reliable)
        next_data = self._extract_from_next_data(soup)
        if next_data:
            print("DEBUG - Found __NEXT_DATA__, using structured data")
            listing_data.update(next_data)
            return listing_data
        
        print("DEBUG - __NEXT_DATA__ not found, falling back to HTML parsing")
        
        # Fallback to HTML parsing
        listing_data['bedrooms'] = self._extract_bedrooms(soup)
        listing_data['bathrooms'] = self._extract_bathrooms(soup)
        listing_data['price'] = self._extract_price(soup)
        listing_data['address'] = self._extract_address(soup)
        
        lat, lon = self._extract_coordinates(soup)
        listing_data['latitude'] = lat
        listing_data['longitude'] = lon
        
        listing_data['laundry'] = self._extract_laundry(soup)
        
        cats_allowed, pets_allowed = self._extract_pet_policy(soup)
        listing_data['cats_allowed'] = cats_allowed
        listing_data['pets_allowed'] = pets_allowed
        
        return listing_data
    
    def _find_key_in_dict(self, obj: dict, target_key: str) -> Optional[any]:
        """Recursively find a key in a nested dictionary"""
        if target_key in obj:
            return obj[target_key]
        
        for key, value in obj.items():
            if isinstance(value, dict):
                result = self._find_key_in_dict(value, target_key)
                if result is not None:
                    return result
        return None
    
    def _extract_from_next_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract data from __NEXT_DATA__ JSON (StreetEasy's structured data)"""
        try:
            script_tag = soup.find('script', id='__NEXT_DATA__')
            if not script_tag or not script_tag.string:
                return None
            
            data = json.loads(script_tag.string)
            
            # Use safe recursive search to find listing data
            listing = (self._find_key_in_dict(data, 'listing') or 
                      self._find_key_in_dict(data, 'listingData') or
                      self._find_key_in_dict(data, 'property'))
            
            if not listing:
                print("DEBUG - __NEXT_DATA__ found but listing data not in expected location")
                return None
            
            result = {}
            
            # Extract structured data
            result['bedrooms'] = listing.get('bedrooms') or listing.get('beds')
            result['bathrooms'] = listing.get('bathrooms') or listing.get('baths')
            
            # Price - handle nested structure
            price_data = listing.get('price')
            if isinstance(price_data, dict):
                result['price'] = price_data.get('amount') or price_data.get('value')
            else:
                result['price'] = price_data or listing.get('rent')
            
            result['address'] = listing.get('address') or listing.get('fullAddress')
            
            # Coordinates
            location = listing.get('location', {})
            result['latitude'] = location.get('latitude') or location.get('lat')
            result['longitude'] = location.get('longitude') or location.get('lng')
            
            # Pet Policy - check for dedicated field first
            pet_policy = listing.get('petPolicy', {})
            if isinstance(pet_policy, dict):
                result['cats_allowed'] = pet_policy.get('cats', False)
                result['pets_allowed'] = pet_policy.get('cats', False) or pet_policy.get('dogs', False)
            else:
                result['cats_allowed'] = None
                result['pets_allowed'] = None
            
            # Amenities - check both list and dict formats
            amenities = listing.get('amenities', [])
            laundry_found = False
            
            if isinstance(amenities, list):
                amenities_lower = []
                amenity_codes = []
                
                for a in amenities:
                    if isinstance(a, dict):
                        # Handle amenity objects with code/name
                        amenities_lower.append(str(a.get('name', '')).lower())
                        code = a.get('code') or a.get('id')
                        if code:
                            amenity_codes.append(str(code))
                    else:
                        amenities_lower.append(str(a).lower())
                
                # Check laundry using codes (15 = washer/dryer, 16 = laundry in building)
                if '15' in amenity_codes or 'WASHER_DRYER' in amenity_codes:
                    result['laundry'] = 'in_unit'
                    laundry_found = True
                elif '16' in amenity_codes or 'LAUNDRY_IN_BUILDING' in amenity_codes:
                    result['laundry'] = 'in_building'
                    laundry_found = True
                
                # Fallback to text matching
                if not laundry_found:
                    if any('in-unit laundry' in a or 'washer/dryer in unit' in a or 'washer dryer' in a for a in amenities_lower):
                        result['laundry'] = 'in_unit'
                    elif any('laundry in building' in a or 'laundry room' in a or 'common laundry' in a for a in amenities_lower):
                        result['laundry'] = 'in_building'
                    else:
                        result['laundry'] = 'none'
                
                # Check pets from amenities if not found in petPolicy
                if result['cats_allowed'] is None:
                    result['pets_allowed'] = any('pet' in a and ('allowed' in a or 'friendly' in a or 'ok' in a) for a in amenities_lower)
                    result['cats_allowed'] = any('cat' in a and ('allowed' in a or 'friendly' in a or 'ok' in a) for a in amenities_lower)
                    
                    # If pets allowed but cats not explicitly mentioned, assume cats included
                    if result['pets_allowed'] and not result['cats_allowed']:
                        if not any('no cat' in a for a in amenities_lower):
                            result['cats_allowed'] = True
            
            if not laundry_found:
                result['laundry'] = 'none'
            
            return result
            
        except Exception as e:
            print(f"DEBUG - Error parsing __NEXT_DATA__: {e}")
            return None
    
    def _get_empty_listing_data(self, url: str) -> Dict:
        """Return empty listing data structure"""
        return {
            'url': url,
            'address': None,
            'bedrooms': None,
            'bathrooms': None,
            'price': None,
            'latitude': None,
            'longitude': None,
            'laundry': None,
            'pets_allowed': None,
            'cats_allowed': None,
        }
    
    def _extract_bedrooms(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract number of bedrooms"""
        page_text = soup.get_text()
        
        # StreetEasy format: "2 rooms | 1 bed | 1 bath" or "2 rooms 1 bed 1 bath"
        # Look for pattern with pipe separator or just spaces
        details_pattern = re.search(r'(\d+)\s+rooms?\s*[|\s]\s*(\d+)\s+beds?', page_text, re.IGNORECASE)
        if details_pattern:
            print(f"DEBUG - Found bedrooms via rooms pattern: {details_pattern.group(2)}")
            return int(details_pattern.group(2))
        
        # Look for "X bed" pattern anywhere (case insensitive, must have number)
        bed_match = re.search(r'(\d+)\s+beds?(?:\s|[|\r\n]|$)', page_text, re.IGNORECASE)
        if bed_match:
            print(f"DEBUG - Found bedrooms: {bed_match.group(1)}")
            return int(bed_match.group(1))
        
        # Look for "studio"
        if re.search(r'\bstudio\b', page_text, re.IGNORECASE):
            # Make sure it's not a false positive
            title_elem = soup.find('h1')
            if title_elem and 'studio' in title_elem.get_text().lower():
                print("DEBUG - Found studio apartment")
                return 0
        
        print("DEBUG - Could not find bedroom count")
        return None
    
    def _extract_bathrooms(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract number of bathrooms"""
        # StreetEasy specific: Look for "X bath" pattern
        page_text = soup.get_text()
        page_text = soup.get_text()
        
        # Look for "X bath" pattern with pipe or space separator
        bath_match = re.search(r'([\d.]+)\s+baths?(?:\s|[|\r\n]|$)', page_text, re.IGNORECASE)
        if bath_match:
            print(f"DEBUG - Found bathrooms: {bath_match.group(1)}")
            return float(bath_match.group(1))
        
        print("DEBUG - Could not find bathroom count")
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract rental price"""
        page_text = soup.get_text()
        
        # StreetEasy format: "$2,500 FOR RENT" or "$2,500FOR RENT"
        price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:FOR\s+)?RENT', page_text, re.IGNORECASE)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            print(f"DEBUG - Found price: ${price_str}")
            return int(float(price_str))
        
        # Fallback: Find any dollar amount in reasonable range ($500-$50,000)
        price_matches = re.findall(r'\$(\d{1,3}(?:,\d{3})*)', page_text)
        for match in price_matches:
            price_str = match.replace(',', '')
            try:
                price = int(price_str)
                # Reasonable apartment rent range
                if 500 <= price <= 50000:
                    print(f"DEBUG - Found price (fallback): ${price}")
                    return price
            except ValueError:
                continue
        
        print("DEBUG - Could not find price")
        return None
    
    def _extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract address"""
        selectors = [
            'h1[class*="building"]',
            '.building-title',
            'h1.incognito',
            'h1',
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                address = elem.get_text().strip()
                if address and len(address) > 5:
                    return address
        
        return None
    
    def _extract_coordinates(self, soup: BeautifulSoup) -> tuple[Optional[float], Optional[float]]:
        """Extract latitude and longitude"""
        # Look for JSON-LD structured data
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'geo' in data:
                    geo = data['geo']
                    return geo.get('latitude'), geo.get('longitude')
            except:
                continue
        
        # Look for data attributes or meta tags
        meta_lat = soup.find('meta', property='place:location:latitude')
        meta_lon = soup.find('meta', property='place:location:longitude')
        
        if meta_lat and meta_lon:
            try:
                return float(meta_lat.get('content')), float(meta_lon.get('content'))
            except:
                pass
        
        # Look in JavaScript variables
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for lat/lng in JavaScript
                lat_match = re.search(r'latitude["\']?\s*:\s*([-\d.]+)', script.string)
                lon_match = re.search(r'longitude["\']?\s*:\s*([-\d.]+)', script.string)
                if lat_match and lon_match:
                    return float(lat_match.group(1)), float(lon_match.group(1))
        
        return None, None
    
    def _extract_laundry(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract laundry information"""
        # Look for amenities section
        page_text = soup.get_text().lower()
        
        # Check for in-unit laundry
        in_unit_patterns = [
            'in-unit laundry', 'in unit laundry', 'washer/dryer in unit',
            'washer and dryer in unit', 'w/d in unit', 'laundry in unit'
        ]
        for pattern in in_unit_patterns:
            if pattern in page_text:
                return 'in_unit'
        
        # Check for in-building laundry
        in_building_patterns = [
            'laundry in building', 'building laundry', 'common laundry',
            'shared laundry', 'laundry room', 'laundry facilities'
        ]
        for pattern in in_building_patterns:
            if pattern in page_text:
                return 'in_building'
        
        # Look in amenities list specifically
        amenities = soup.find_all(class_=re.compile('amenity|feature', re.I))
        for amenity in amenities:
            text = amenity.get_text().lower()
            for pattern in in_unit_patterns:
                if pattern in text:
                    return 'in_unit'
            for pattern in in_building_patterns:
                if pattern in text:
                    return 'in_building'
        
        return 'none'
    
    def _extract_pet_policy(self, soup: BeautifulSoup) -> tuple[bool, bool]:
        """Extract pet policy, returns (cats_allowed, pets_allowed)"""
        page_text = soup.get_text().lower()
        
        cats_allowed = False
        pets_allowed = False
        
        # Check for explicit cat mentions
        if any(phrase in page_text for phrase in ['cats allowed', 'cats ok', 'cat friendly']):
            cats_allowed = True
            pets_allowed = True
        
        # Check for pets allowed generally
        if any(phrase in page_text for phrase in ['pets allowed', 'pets ok', 'pet friendly', 'dogs and cats']):
            pets_allowed = True
            # If pets allowed generally, assume cats are included unless explicitly stated otherwise
            if 'no cats' not in page_text and 'cats not allowed' not in page_text:
                cats_allowed = True
        
        # Check for no pets
        if any(phrase in page_text for phrase in ['no pets', 'pets not allowed', 'no dogs or cats']):
            cats_allowed = False
            pets_allowed = False
        
        # Look in specific pet policy sections
        pet_sections = soup.find_all(class_=re.compile('pet|policy', re.I))
        for section in pet_sections:
            text = section.get_text().lower()
            if 'cats allowed' in text or 'cats ok' in text:
                cats_allowed = True
                pets_allowed = True
            elif 'pets allowed' in text or 'pets ok' in text:
                pets_allowed = True
                if 'no cats' not in text:
                    cats_allowed = True
        
        return cats_allowed, pets_allowed
    
    def validate_requirements(self, listing: Dict) -> tuple[bool, list[str]]:
        """
        Check if listing meets basic requirements
        
        Args:
            listing: Listing data dictionary
            
        Returns:
            Tuple of (meets_requirements, failed_requirements)
        """
        failed = []
        
        # Check bedrooms (1 or 2)
        if listing.get('bedrooms') not in [1, 2]:
            failed.append(f"Bedrooms: {listing.get('bedrooms')} (need 1 or 2)")
        
        # Check laundry (in unit or in building)
        if listing.get('laundry') not in ['in_unit', 'in_building']:
            failed.append(f"Laundry: {listing.get('laundry')} (need in_unit or in_building)")
        
        # Check cats allowed
        if not listing.get('cats_allowed'):
            failed.append("Cats not allowed")
        
        meets_requirements = len(failed) == 0
        return meets_requirements, failed
