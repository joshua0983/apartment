// Use the correct API namespace (chrome or browser)
const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

// Load saved API URL
browserAPI.storage.sync.get(['apiUrl'], (result) => {
  if (result.apiUrl) {
    document.getElementById('apiUrl').value = result.apiUrl;
  }
});

// Save API URL when changed
document.getElementById('apiUrl').addEventListener('change', (e) => {
  browserAPI.storage.sync.set({ apiUrl: e.target.value });
});

// Evaluate button handler
document.getElementById('evaluateBtn').addEventListener('click', async () => {
  const statusDiv = document.getElementById('status');
  const resultsDiv = document.getElementById('results');
  const evaluateBtn = document.getElementById('evaluateBtn');
  
  // Get current tab
  const [tab] = await browserAPI.tabs.query({ active: true, currentWindow: true });
  
  // Show loading state
  statusDiv.className = 'status loading';
  statusDiv.textContent = '🔍 Extracting address from page...';
  evaluateBtn.disabled = true;
  resultsDiv.style.display = 'none';
  
  try {
    // Extract address from current page using content script
    console.log('[Popup] Sending extractAddress message to content script...');
    const response = await browserAPI.tabs.sendMessage(tab.id, { action: 'extractAddress' });
    console.log('[Popup] Received response from content script:', response);
    
    if (!response || !response.address) {
      throw new Error('Could not find an address on this page. Make sure you\'re on a rental listing.');
    }
    
    console.log('[Popup] Extracted address:', response.address);
    statusDiv.textContent = `📍 Found address: ${response.address}. Evaluating...`;
    
    // Get API URL from settings
    const { apiUrl } = await browserAPI.storage.sync.get(['apiUrl']);
    const serverUrl = apiUrl || 'http://localhost:8000';
    console.log('[Popup] Using API server:', serverUrl);
    
    // Call backend API
    console.log('[Popup] Calling API...');
    const apiResponse = await fetch(`${serverUrl}/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ address: response.address })
    });
    
    console.log('[Popup] API response status:', apiResponse.status);
    
    if (!apiResponse.ok) {
      const errorText = await apiResponse.text();
      console.error('[Popup] API error response:', errorText);
      try {
        const errorData = JSON.parse(errorText);
        throw new Error(errorData.detail || 'API request failed');
      } catch (e) {
        throw new Error(`API request failed: ${errorText}`);
      }
    }
    
    const evaluation = await apiResponse.json();
    
    // Debug: log the full response
    console.log('[Popup] Evaluation response:', evaluation);
    
    // Display results
    displayResults(evaluation);
    
    statusDiv.className = 'status success';
    statusDiv.textContent = '✅ Evaluation complete!';
    resultsDiv.style.display = 'block';
    
  } catch (error) {
    statusDiv.className = 'status error';
    statusDiv.textContent = `❌ Error: ${error.message}`;
    console.error('Evaluation error:', error);
  } finally {
    evaluateBtn.disabled = false;
  }
});

function displayResults(evaluation) {
  // Score
  const scoreElement = document.getElementById('score');
  scoreElement.textContent = evaluation.score.toFixed(2);
  
  // Cached indicator
  const cachedIndicator = document.getElementById('cached-indicator');
  if (evaluation.cached) {
    cachedIndicator.innerHTML = '<span class="cached-badge">CACHED</span>';
  } else {
    cachedIndicator.innerHTML = '';
  }
  
  // Commutes
  const commutesDiv = document.getElementById('commutes');
  commutesDiv.innerHTML = '';
  Object.entries(evaluation.commutes).forEach(([office, data]) => {
    const duration = data.duration_minutes || 'N/A';
    const className = data.meets_preference ? 'good' : 'warning';
    commutesDiv.innerHTML += `
      <div class="detail-row">
        <span class="detail-label">${office}</span>
        <span class="detail-value ${className}">${duration}${duration !== 'N/A' ? ' min' : ''}</span>
      </div>
    `;
  });
  
  // Subway
  const subwayDiv = document.getElementById('subway');
  const subwayClass = evaluation.subway.meets_preference ? 'good' : 'warning';
  subwayDiv.innerHTML = `
    <div class="detail-row">
      <span class="detail-label">Station</span>
      <span class="detail-value">${evaluation.subway.station_name}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Walk Time</span>
      <span class="detail-value ${subwayClass}">${evaluation.subway.walk_time_minutes} min</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Lines</span>
      <span class="detail-value">${evaluation.subway.lines.join(', ')}</span>
    </div>
  `;
  
  // Amenities
  const amenitiesDiv = document.getElementById('amenities');
  amenitiesDiv.innerHTML = `
    <div class="detail-row">
      <span class="detail-label">Total Nearby</span>
      <span class="detail-value">${evaluation.amenities.total_amenities}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Restaurants</span>
      <span class="detail-value">${evaluation.amenities.restaurants}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Cafes</span>
      <span class="detail-value">${evaluation.amenities.cafes}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Bars</span>
      <span class="detail-value">${evaluation.amenities.bars}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Bubble Tea</span>
      <span class="detail-value">${evaluation.amenities.bubble_tea}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Density Score</span>
      <span class="detail-value">${evaluation.amenities.amenity_density_score}/10</span>
    </div>
  `;
  
  // Breakdown
  const breakdownDiv = document.getElementById('breakdown');
  breakdownDiv.innerHTML = `
    <div class="detail-row">
      <span class="detail-label">Commute (40%)</span>
      <span class="detail-value">${evaluation.breakdown.commute_score.toFixed(2)}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Subway (30%)</span>
      <span class="detail-value">${evaluation.breakdown.subway_score.toFixed(2)}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Amenities (20%)</span>
      <span class="detail-value">${evaluation.breakdown.amenities_score.toFixed(2)}</span>
    </div>
    <div class="detail-row">
      <span class="detail-label">Bonus (10%)</span>
      <span class="detail-value">${evaluation.breakdown.bonus.toFixed(2)}</span>
    </div>
  `;
}
