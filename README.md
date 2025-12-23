# Apartment Location Evaluator

A Python tool that evaluates apartment locations based on commute times, subway proximity, and nearby amenities.

## Features

- **Commute Analysis**: Calculate transit times to 3 office locations using Google Maps Distance Matrix API
- **Subway Proximity**: Find nearest NYC subway station with walking time
- **Amenity Analysis**: Discover nearby restaurants, cafes, bars, and bubble tea shops
- **Automated Scoring**: Get a rating from 0.00 to 5.00 based on weighted criteria

## Requirements

- Python 3.8+
- Google Maps API key (Distance Matrix, Places & Geocoding API enabled)

## Setup

1. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API key**:
   Create a `.env` file in the project root:
   ```bash
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

3. **Get Google Maps API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)
   - Create a new project or select existing
   - Enable these APIs:
     - Distance Matrix API
     - Places API
     - Geocoding API
   - Create credentials (API Key)
   - Copy the key to `.env`

4. **Configure office locations**:
   Edit `src/commute.py` to add your office addresses or Google Maps share links

## Usage

### Command Line

Run the evaluator with an address:

```bash
python test_address.py "123 Main St, Queens, NY 11101"
```

Or use the main module directly:

```bash
cd src
python main.py "34-20 30th Street, Queens, NY 11101"
```

### As a Module

```python
from src.main import evaluate_address

result = evaluate_address("34-20 30th Street, Queens, NY 11101")
print(f"Score: {result['score']}/5.00")
```

Results will be saved to `output/evaluation_TIMESTAMP.json`

## Configuration

Edit `config.py` to customize:
- Office locations for commute calculations
- Apartment requirements (bedrooms, laundry, pets)
- Scoring weights
- Preferences (max commute time, etc.)

## Project Structure

```
apartment/
├── src/
│   ├── main.py           # Entry point
│   ├── scraper.py        # StreetEasy scraper
│   ├── commute.py        # Commute calculator
│   ├── proximity.py      # Transit & amenities analyzer
│   └── scorer.py         # Scoring algorithm
├── data/                 # Subway station data, caches
├── output/               # Evaluation results
├── config.py             # Configuration
├── requirements.txt      # Python dependencies
└── .env                  # API keys (not in git)
```

## Scoring Algorithm

The tool rates apartments on a 0.00-5.00 scale using weighted criteria:

- **Commute Time** (40%): Shorter commutes to offices score higher
- **Subway Proximity** (30%): Closer subway stations score higher
- **Amenities** (20%): Better access to restaurants/shops scores higher
- **Bonus** (10%): Extra points for meeting all preferences

Apartments that don't meet basic requirements receive a score of 0.00.

## Next Steps

Current implementation has placeholder functions. To complete:

1. Implement StreetEasy scraping (BeautifulSoup or Selenium)
2. Add Google Maps API integration for commute calculations
3. Load/download NYC subway station data
4. Implement Google Places API for amenities analysis
5. Test with real listings
6. Consider converting to VS Code extension

## License

Personal use project
