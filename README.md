# NYC Apartment Location Evaluator

A comprehensive tool for evaluating NYC apartment locations with a **REST API backend** and **browser extension** that automatically analyzes rental listings based on commute times, transit access, and amenities.

## Features

- **🚀 Browser Extension**: Automatically evaluate apartments on StreetEasy, Zillow, Apartments.com, and RentHop
- **⚡ Async REST API**: FastAPI backend with parallel Google Maps API calls (~1 second per evaluation)
- **🚇 Subway Proximity**: Find nearest NYC subway station with walking time
- **🚌 Commute Analysis**: Calculate transit times to 4 office locations using Google Maps
- **🍽️ Amenity Analysis**: Discover nearby restaurants, cafes, bars, and bubble tea shops  
- **📊 Automated Scoring**: Get a rating from 0.00 to 5.00 based on weighted criteria
- **💾 Smart Caching**: Instant responses for previously evaluated addresses (24-hour TTL)

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

## Quick Start

### 1. Browser Extension (Recommended)

The easiest way to use this tool:

```bash
# Install dependencies and start API server
pip install -r requirements.txt
python -m uvicorn api.server:app --reload

# In another terminal, set up the extension
cd extension
python3 create_icons.py

# Load extension in Chrome:
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked" → select the extension folder
```

Then visit any rental listing and click the extension icon!

See [extension/README.md](extension/README.md) for detailed instructions.

### 2. REST API

Start the API server:

```bash
python -m uvicorn api.server:app --reload
```

Evaluate an address via API:

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"address": "34-20 30th Street, Queens, NY 11101"}'
```

API Documentation: http://localhost:8000/docs

### 3. Command Line

Run the evaluator directly with an address:

```bash
python test_address.py "123 Main St, Queens, NY 11101"
```

Or use the async version for faster results:

```bash
cd src
python main_async.py "34-20 30th Street, Queens, NY 11101"
```

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
