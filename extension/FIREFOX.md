# Firefox Installation Instructions

## Issue: Manifest V3 Support

Firefox has limited support for Manifest V3 service workers. The extension now uses cross-browser compatible code.

## Installation Steps for Firefox

### Option 1: Use the Updated Extension (Recommended)

The extension has been updated to be compatible with both Chrome and Firefox:

1. **Open Firefox**
2. **Go to** `about:debugging#/runtime/this-firefox`
3. **Click** "Load Temporary Add-on..."
4. **Navigate to** the extension folder: `/Users/joshuajateno/Documents/GitHub/apartment/extension`
5. **Select** `manifest.json`
6. **Click** "Open"

The extension should now load without errors!

### Option 2: Use Manifest V2 (Alternative)

If you still encounter issues, use the Firefox-specific manifest:

1. In the extension folder, **rename files**:
   ```bash
   cd /Users/joshuajateno/Documents/GitHub/apartment/extension
   mv manifest.json manifest-chrome.json
   mv manifest-firefox.json manifest.json
   ```

2. **Load the extension** as described in Option 1

3. **To switch back to Chrome**, reverse the rename:
   ```bash
   mv manifest.json manifest-firefox.json
   mv manifest-chrome.json manifest.json
   ```

## What Was Fixed

The extension now includes:

✅ Cross-browser compatible code using `const browserAPI = typeof browser !== 'undefined' ? browser : chrome;`  
✅ Works with both Manifest V3 (Chrome) and Firefox's implementation  
✅ Updated `background.js`, `popup.js`, and `content.js` for compatibility

## Testing in Firefox

1. **Start the API server**:
   ```bash
   cd /Users/joshuajateno/Documents/GitHub/apartment
   source venv/bin/activate
   python -m uvicorn api.server:app --reload
   ```

2. **Load the extension** (see steps above)

3. **Visit a rental listing** (e.g., StreetEasy, Zillow)

4. **Click the extension icon** in the toolbar

5. **Click "Evaluate This Page"**

## Troubleshooting

### "background.service_worker is currently disabled"
- This error is expected with older Firefox versions
- Use the updated manifest.json which now has cross-browser support

### Extension icon doesn't show
- Look for the puzzle piece icon in Firefox toolbar
- Or go to `about:addons` → Extensions → NYC Apartment Evaluator

### Permissions issues
- Firefox may show additional permission warnings
- Click "Accept" to grant necessary permissions

### Can't connect to localhost
- Make sure the API server is running
- Check http://localhost:8000/health in Firefox
- Firefox may have stricter localhost security - this should work fine

## Differences from Chrome

- Firefox temporary add-ons are removed when you close Firefox
- Need to reload each time you restart the browser
- Some Manifest V3 features may behave slightly differently

## Production Deployment

For a permanent Firefox extension:
1. Package the extension as a .xpi file
2. Submit to Firefox Add-ons store
3. Or use Firefox Developer Edition for self-hosting

## Questions?

Check the main [INSTALLATION.md](../INSTALLATION.md) or extension [README.md](README.md) for more details.
