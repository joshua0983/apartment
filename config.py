"""
Configuration for apartment evaluator
"""

# Office locations to check commutes
OFFICE_LOCATIONS = {
    'office_1': {
        'name': 'Office 1',
        'url': 'https://maps.app.goo.gl/Sd2hgHavdZbKBcw19',
        'coordinates': None,  # TODO: Extract from Google Maps link
    },
    'office_2': {
        'name': 'Office 2',
        'url': 'https://maps.app.goo.gl/AWLA9pQ7VHrcjZzU9',
        'coordinates': None,  # TODO: Extract from Google Maps link
    },
    'office_3': {
        'name': 'Office 3',
        'url': 'https://maps.app.goo.gl/4yS8EqFvCW45pamp7',
        'coordinates': None,  # TODO: Extract from Google Maps link
    },
}

# Apartment requirements
REQUIREMENTS = {
    'bedrooms': [1, 2],  # Must be 1 or 2 bedrooms
    'laundry': ['in_unit', 'in_building'],  # Must have in-unit or in-building laundry
    'cats_allowed': True,  # Must allow cats
}

# Preferences (not hard requirements)
PREFERENCES = {
    'max_commute_minutes': 30,  # Preferred max commute time
    'max_subway_walk_minutes': 5,  # Preferred max walk to subway
}

# Scoring weights (must sum to 1.0)
SCORING_WEIGHTS = {
    'commute': 0.40,
    'subway_proximity': 0.30,
    'amenities': 0.20,
    'requirements_bonus': 0.10,
}

# Scraping settings
SCRAPER_CONFIG = {
    'use_selenium': False,  # Use Selenium for JavaScript-heavy pages
    'timeout': 10,  # Seconds
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
}
