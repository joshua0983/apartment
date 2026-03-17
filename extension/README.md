# NYC Apartment Evaluator - Browser Extension

A standalone Chrome/Firefox extension that automatically evaluates NYC apartment listings based on commute times, transit access, and amenities.

No backend server or Python installation required! Everything runs directly in the browser.

## Features

✅ **Automatic address extraction** from rental listing pages  
✅ **Real-time evaluation** using Google Maps API directly  
✅ **Commute Times** to your customizable office locations  
✅ **Subway Proximity** analysis using embedded station data  
✅ **Detailed scoring** (0-5.00 scale)  
✅ **Multi-site support** - StreetEasy, Zillow, Apartments.com, RentHop

## Setup Guide

### 1. Requirements

- A Google Maps API Key with the following APIs enabled:
  - **Distance Matrix API** (for commute times)
  - **Geocoding API** (for address lookup)
  - **Places API (New)** or **Places API** (for amenity analysis)

> **Note:** Billing must be enabled on your Google Cloud project for these APIs to work, even within the free tier.

### 2. Installation (Chrome/Edge/Brave)

1. Download this `extension` folder (unzip if necessary).
2. Open Chrome and go to `chrome://extensions/`.
3. Enable **"Developer mode"** (toggle in top-right).
4. Click **"Load unpacked"**.
5. Select the `extension` folder.

### 3. Configuration

1. Once installed, the **Options Page** should open automatically. If not, right-click the extension icon and select "Options".
2. Enter your **Google Maps API Key**.
3. (Optional) Customize your **Office Locations** in the JSON editor.
4. Click **Save Settings**.

## Usage

1. **Navigate to a rental listing** on StreetEasy, Zillow, etc.
2. **Click the extension icon** in your toolbar.
3. The extension will automatically find the address and display "Found address: ...".
4. Results appear instantly!

## Troubleshooting

- **"No API Key configured"**: Make sure you saved your key in the Options page.
- **API Errors**: Ensure your Google Cloud Project has billing enabled and the correct APIs (Distance Matrix, Geocoding) are enabled.
- **Address not found**: Try refreshing the page or navigating to the specific listing detail page.

## Data Privacy

This extension runs locally in your browser. Your API key and office locations are stored in your browser's local sync storage and are never sent to any third-party server (other than directly to Google Maps for evaluation).
