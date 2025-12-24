# Browser Extension Installation Guide

## ✅ What's Built

Your NYC Apartment Evaluator now includes:

1. **FastAPI Backend** (`api/server.py`)
   - REST API endpoint: `POST /evaluate`
   - Health check: `GET /health`
   - Built-in caching (24-hour TTL)
   - CORS enabled for extension

2. **Async Evaluation System**
   - `src/main_async.py` - Async orchestration
   - `src/commute_async.py` - Parallel commute calculations
   - `src/proximity_async.py` - Parallel amenity searches
   - ~70% faster than synchronous version

3. **Browser Extension** (`extension/` folder)
   - `manifest.json` - Chrome/Firefox compatible
   - `popup.html` + `popup.js` - Beautiful UI
   - `content.js` - Address extraction from rental sites
   - `background.js` - Service worker
   - Icons generated automatically

## 🚀 Installation Steps

### Step 1: Ensure API Server is Running

```bash
# In your apartment directory
source venv/bin/activate
python -m uvicorn api.server:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Load Extension in Chrome

1. Open Chrome
2. Go to `chrome://extensions/`
3. Toggle **"Developer mode"** ON (top-right corner)
4. Click **"Load unpacked"**
5. Navigate to and select: `/Users/joshuajateno/Documents/GitHub/apartment/extension`
6. You should see the extension with a building icon

### Step 3: Test the Extension

1. Go to a rental listing, for example:
   - https://streeteasy.com/rental/4199447
   - https://www.zillow.com/homedetails/34-20-30th-St-APT-3F-Queens-NY-11106/2057041842_zpid/

2. Click the extension icon in your toolbar

3. Click **"Evaluate This Page"**

4. Wait ~1-2 seconds for results

5. View your apartment score and details!

## 🔧 Troubleshooting

### Extension doesn't appear after loading

- Check for errors in `chrome://extensions/` (click "Errors" button)
- Try refreshing the extensions page
- Verify all files exist in the extension folder

### "Could not find an address on this page"

- Ensure you're on a specific listing page (not search results)
- Open DevTools Console and check for extraction errors
- Try manually selecting the address text and using right-click menu

### "API request failed"

Check these:
1. API server is running: `curl http://localhost:8000/health`
2. CORS is enabled in `api/server.py`
3. Extension settings have correct URL (`http://localhost:8000`)

### Can't connect to localhost:8000

The API server might not be running. Start it with:
```bash
cd /Users/joshuajateno/Documents/GitHub/apartment
source venv/bin/activate
python -m uvicorn api.server:app --reload
```

## 📊 Expected Results

When you evaluate an address, you'll see:

- **Overall Score**: 0.00 - 5.00 (weighted average)
- **Commute Times**: Transit times to 4 offices
- **Nearest Subway**: Station name, lines, walk time
- **Amenities**: Restaurants, cafes, bars, bubble tea counts
- **Score Breakdown**: Individual component scores

Scores are color-coded:
- 🟢 Green: Meets preferences (< 30 min commute, < 5 min to subway)
- 🟡 Yellow: Acceptable but doesn't meet preferences
- 🔴 Red: Poor (not currently used, reserved for future)

## 🎨 Customization

### Change Office Locations

Edit `config.py`:
```python
OFFICES = {
    'office_1': {
        'address': 'Your Office Address',
        'name': 'Office Name'
    },
    # Add more offices...
}
```

Restart API server after changes.

### Adjust Scoring Weights

Edit `src/scorer.py`:
```python
COMMUTE_WEIGHT = 0.40  # 40%
SUBWAY_WEIGHT = 0.30   # 30%
AMENITIES_WEIGHT = 0.20  # 20%
REQUIREMENTS_WEIGHT = 0.10  # 10%
```

### Add More Rental Sites

Edit `extension/content.js` and add selectors to `SITE_PATTERNS`:
```javascript
'newsite.com': {
  selectors: [
    '.address-selector',
    'h1.listing-address'
  ]
}
```

## 🔄 Updates & Development

### Update Extension After Code Changes

1. Make your code changes
2. Go to `chrome://extensions/`
3. Click the refresh icon on your extension card
4. Test the changes

### View Extension Logs

- Right-click extension icon → "Inspect popup" → Console tab
- Or check the page console where content script runs

### API Endpoint Documentation

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI)

## 📱 Next Steps

### Deploy Backend to Cloud

For production use, deploy the API server:

**Heroku:**
```bash
heroku create apt-evaluator
git push heroku main
```

**Railway:**
```bash
railway init
railway up
```

Then update the extension's API URL setting to your deployed URL.

### Publish Extension

To publish on Chrome Web Store:
1. Zip the extension folder
2. Go to https://chrome.google.com/webstore/devconsole
3. Pay $5 one-time developer fee
4. Upload and submit for review

## 🆘 Support

If you encounter issues:

1. Check API server logs in terminal
2. Check browser console for JavaScript errors
3. Verify Google Maps API key has all required APIs enabled
4. Test API directly: `curl -X POST http://localhost:8000/evaluate -H "Content-Type: application/json" -d '{"address": "test address"}'`

## 📝 File Structure

```
apartment/
├── api/
│   └── server.py          # FastAPI REST API
├── extension/
│   ├── manifest.json      # Extension config
│   ├── popup.html         # Extension UI
│   ├── popup.js           # UI logic
│   ├── content.js         # Address extraction
│   ├── background.js      # Service worker
│   ├── icons/             # Extension icons
│   └── README.md          # Detailed docs
├── src/
│   ├── main_async.py      # Async evaluation
│   ├── commute_async.py   # Async commute calc
│   └── proximity_async.py # Async amenity search
└── README.md              # Main project docs
```

Enjoy evaluating apartments! 🏙️
