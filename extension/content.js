// Address extraction patterns for different rental sites
// Compatible with both Chrome and Firefox
const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

const SITE_PATTERNS = {
  'streeteasy.com': {
    selectors: [
      'h1',  // Main heading usually has the street address
      '.BuildingInfo-address',
      '[itemprop="streetAddress"]'
    ],
    // StreetEasy-specific: extract neighborhood from breadcrumbs
    extraInfo: () => {
      console.log('[Content] StreetEasy: Looking for neighborhood info...');
      
      // Skip common UI terms that aren't locations
      const skipTerms = ['rent', 'buy', 'sell', 'rentals', 'sales', 'new york', 'home', 'search', 'apartments', 'building'];
      
      // Known NYC boroughs and neighborhoods
      const nycLocations = ['astoria', 'queens', 'brooklyn', 'manhattan', 'bronx', 'staten island',
                           'williamsburg', 'greenpoint', 'bushwick', 'park slope', 'prospect heights',
                           'crown heights', 'bed-stuy', 'bedford-stuyvesant', 'harlem', 'upper east side',
                           'upper west side', 'midtown', 'downtown', 'financial district', 'tribeca',
                           'soho', 'chelsea', 'gramercy', 'murray hill', 'east village', 'west village',
                           'greenwich village', 'lower east side', 'ues', 'uws', 'fidi', 'dumbo',
                           'long island city', 'lic', 'sunnyside', 'woodside', 'jackson heights',
                           'forest hills', 'rego park', 'kew gardens', 'flushing', 'bayside', 'ridgewood'];
      
      // Try specific breadcrumb selectors first
      let breadcrumbs = document.querySelectorAll('.Breadcrumbs a, [aria-label="breadcrumbs"] a, .breadcrumbs a');
      
      // Fallback to all nav links if no specific breadcrumbs found
      if (breadcrumbs.length === 0) {
        console.log('[Content] No specific breadcrumbs found, checking all nav links...');
        breadcrumbs = document.querySelectorAll('nav a, .nav a');
      }
      
      console.log('[Content] Found potential location links:', breadcrumbs.length);
      
      let foundLocations = [];
      
      for (let crumb of breadcrumbs) {
        const text = crumb.textContent.trim();
        const textLower = text.toLowerCase();
        
        // Skip common UI terms
        if (skipTerms.includes(textLower) || text.length < 3) {
          continue;
        }
        
        // Check if it's a known NYC location
        if (nycLocations.includes(textLower)) {
          console.log('[Content] Found candidate location:', text);
          foundLocations.push(text);
        }
      }
      
      // Return the LAST found location as it's likely the most specific (neighborhood)
      // Breadcrumbs usually go: Home > NYC > Borough > Neighborhood
      if (foundLocations.length > 0) {
        const bestLocation = foundLocations[foundLocations.length - 1];
        console.log('[Content] Selected most specific location:', bestLocation);
        return bestLocation + ', NY';
      }
      
      console.log('[Content] No neighborhood found, using fallback');
      return 'NY'; 
    }
  },
  'zillow.com': {
    selectors: [
      '[data-testid="property-address"]',
      'h1[data-testid="bdp-building-address"]',
      '.ds-address-container h1',
      'h1.sc-address',
      '[data-rf-test-id="abp-streetLine"]'
    ]
  },
  'apartments.com': {
    selectors: [
      '[data-tag_section="address"]',
      '.propertyAddressContainer',
      'h1.propertyName',
      '.propertyAddress',
      '[itemprop="address"]'
    ]
  },
  'renthop.com': {
    selectors: [
      '.font-size-heading-1',
      '.listing-address',
      'h1.address',
      '[itemprop="streetAddress"]'
    ]
  }
};

// Listen for messages from popup
browserAPI.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractAddress') {
    const address = extractAddress();
    sendResponse({ address });
  }
  return true; // Keep message channel open for async response
});

function extractAddress() {
  const hostname = window.location.hostname;
  
  // Determine which site we're on
  let siteConfig = null;
  for (const [site, config] of Object.entries(SITE_PATTERNS)) {
    if (hostname.includes(site)) {
      siteConfig = config;
      break;
    }
  }
  
  if (!siteConfig) {
    console.warn('Unknown rental site:', hostname);
    return tryGenericExtraction();
  }
  
  // Try each selector for this site
  for (const selector of siteConfig.selectors) {
    const element = document.querySelector(selector);
    if (element) {
      let address = element.textContent.trim();
      
      // For StreetEasy, add neighborhood/borough info
      if (hostname.includes('streeteasy.com') && siteConfig.extraInfo) {
        console.log('[Content] This is StreetEasy, calling extraInfo...');
        const extraInfo = siteConfig.extraInfo();
        console.log('[Content] extraInfo returned:', extraInfo);
        console.log('[Content] Current address:', address);
        
        if (extraInfo && !address.toLowerCase().includes(extraInfo.toLowerCase())) {
          address += ', ' + extraInfo;
          console.log('[Content] Updated address with extraInfo:', address);
        } else {
          console.log('[Content] Not adding extraInfo (already included or empty)');
        }
      }
      
      // Clean up the address
      address = cleanAddress(address);
      
      if (address && address.length > 10) {
        console.log('[Content] Found address:', address, 'using selector:', selector);
        return address;
      }
    }
  }
  
  // Fallback to generic extraction
  return tryGenericExtraction();
}

function tryGenericExtraction() {
  // Try to find address in meta tags
  const metaAddress = document.querySelector('meta[property="og:street-address"]');
  if (metaAddress) {
    return cleanAddress(metaAddress.content);
  }
  
  // Try schema.org structured data
  const schemaAddress = document.querySelector('[itemprop="streetAddress"]');
  if (schemaAddress) {
    return cleanAddress(schemaAddress.textContent);
  }
  
  // Try to find address-like text patterns in the page
  const bodyText = document.body.innerText;
  const addressPattern = /\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Way|Pkwy|Parkway),?\s*(?:New York|NY|Brooklyn|Queens|Bronx|Manhattan|Staten Island)/gi;
  const matches = bodyText.match(addressPattern);
  
  if (matches && matches.length > 0) {
    return cleanAddress(matches[0]);
  }
  
  return null;
}

function cleanAddress(address) {
  if (!address) return null;
  
  // Remove extra whitespace
  address = address.replace(/\s+/g, ' ').trim();
  
  // Remove common prefixes
  address = address.replace(/^(Address:|Location:|Property Address:)\s*/i, '');
  
  // Remove extra line breaks or special characters
  address = address.replace(/[\n\r\t]/g, ' ');
  
  // Ensure it has New York or NY
  if (!address.match(/\b(New York|NY)\b/i)) {
    // Try to add NY if we have a borough
    if (address.match(/\b(Brooklyn|Queens|Bronx|Manhattan|Staten Island)\b/i)) {
      address += ', NY';
    }
  }
  
  return address;
}

// Inject evaluation badge on page (optional - for visual feedback)
function injectEvaluationBadge(score) {
  // Remove existing badge if present
  const existingBadge = document.getElementById('apt-eval-badge');
  if (existingBadge) {
    existingBadge.remove();
  }
  
  // Create badge
  const badge = document.createElement('div');
  badge.id = 'apt-eval-badge';
  badge.innerHTML = `
    <div style="position: fixed; top: 20px; right: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 999999; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
      <div style="font-size: 12px; opacity: 0.9;">NYC Apartment Score</div>
      <div style="font-size: 32px; font-weight: bold; margin-top: 4px;">${score.toFixed(2)}</div>
      <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">out of 5.00</div>
    </div>
  `;
  
  document.body.appendChild(badge);
  
  // Auto-remove after 10 seconds
  setTimeout(() => {
    badge.style.transition = 'opacity 0.5s';
    badge.style.opacity = '0';
    setTimeout(() => badge.remove(), 500);
  }, 10000);
}

// Listen for evaluation results to show badge
browserAPI.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showBadge' && request.score) {
    injectEvaluationBadge(request.score);
  }
});
