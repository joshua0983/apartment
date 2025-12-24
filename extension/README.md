# NYC Apartment Evaluator - Browser Extension

Chrome/Firefox extension that automatically evaluates NYC apartment listings based on commute times, transit access, and amenities.

## Quick Start

### 1. Generate Extension Icons

```bash
cd extension
python3 create_icons.py
```

### 2. Start the Backend API

```bash
cd ..
source venv/bin/activate
python -m uvicorn api.server:app --reload
```

The API server will run on `http://localhost:8000`

### 3. Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable **"Developer mode"** (toggle in top-right)
3. Click **"Load unpacked"**
4. Select the `extension` folder
5. The extension icon should appear in your toolbar

### 4. Load Extension in Firefox

1. Open Firefox and go to `about:debugging#/runtime/this-firefox`
2. Click **"Load Temporary Add-on"**
3. Navigate to the `extension` folder and select `manifest.json`

## Usage

1. **Navigate to a rental listing** on:
   - StreetEasy
   - Zillow
   - Apartments.com
   - RentHop

2. **Click the extension icon** in your browser toolbar

3. **Click "Evaluate This Page"**

4. **View the results**:
   - Overall score (0-5.00)
   - Commute times to your offices
   - Nearest subway station with walk time
   - Nearby amenities count
   - Detailed score breakdown

## Features

✅ **Automatic address extraction** from rental listing pages  
✅ **Real-time evaluation** with loading states and error handling  
✅ **Cached results** - Instant response for previously evaluated addresses  
✅ **Detailed breakdown** - Commute, subway, amenities, and bonus scores  
✅ **Color-coded metrics** - Green (good), Yellow (warning), Red (poor)  
✅ **Configurable API URL** - Works with local or deployed backend  
✅ **Multi-site support** - StreetEasy, Zillow, Apartments.com, RentHop

## Configuration

### Change API Server URL

1. Click the extension icon
2. Scroll down to "API Server URL"
3. Update the URL (default: `http://localhost:8000`)
4. Changes are saved automatically

### Customize Office Locations

Edit the office locations in `config.py` in the main project directory, then restart the API server.

## Architecture

```
Browser Extension                Python Backend
┌─────────────────┐             ┌──────────────────┐
│  content.js     │────────────▶│  api/server.py   │
│  (extract addr) │             │  (FastAPI)       │
└────────┬────────┘             └────────┬─────────┘
         │                               │
         ▼                               ▼
┌─────────────────┐             ┌──────────────────┐
│  popup.js       │◀────────────│  src/main_async │
│  (display UI)   │  JSON resp  │  (evaluation)    │
└─────────────────┘             └────────┬─────────┘
                                         │
                                         ▼
                                ┌──────────────────┐
                                │  Google Maps API │
                                └──────────────────┘
```

## Supported Sites

| Site | Status | Address Detection |
|------|--------|-------------------|
| **StreetEasy** | ✅ Full Support | Multiple selectors |
| **Zillow** | ✅ Full Support | Multiple selectors |
| **Apartments.com** | ✅ Full Support | Multiple selectors |
| **RentHop** | ✅ Full Support | Multiple selectors |
| **Other sites** | ⚠️ Generic | Regex pattern matching |

## Troubleshooting

### "Could not find an address on this page"

- Make sure you're on a **specific listing page** (not search results)
- Try refreshing the page
- Check browser console for selector errors

### "API request failed"

- Ensure the Python backend is running: `uvicorn api.server:app --reload`
- Check that the API URL in settings matches your backend URL
- Verify your Google Maps API key is set in `.env`
- Check terminal for backend errors

### Extension not appearing

- Refresh the `chrome://extensions/` page
- Check browser console for JavaScript errors
- Try reloading the extension (click the reload icon)

### Scores seem incorrect

- Verify your office locations in `config.py` are correct
- Check the API response in browser DevTools Network tab
- Ensure Google Maps API key has necessary permissions enabled

## Development

### Testing Address Extraction

Open DevTools Console on a rental listing page and run:
```javascript
chrome.runtime.sendMessage({action: 'extractAddress'}, (response) => {
  console.log('Extracted:', response.address);
});
```

### Debugging API Calls

Check the Network tab in DevTools to see requests to `http://localhost:8000/evaluate`

### Modifying Site Patterns

Edit `content.js` and add/update selectors in the `SITE_PATTERNS` object for better address extraction.

## Next Steps

- [ ] Deploy backend to cloud (Heroku, Railway, DigitalOcean)
- [ ] Add user authentication for API access
- [ ] Allow custom office locations per user
- [ ] Add comparison mode for multiple apartments
- [ ] Export results to CSV/PDF
- [ ] Add neighborhood insights (crime, schools, etc.)

## License

MIT
