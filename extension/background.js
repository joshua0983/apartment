// Background service worker - NYC Apartment Evaluator
// Minimal implementation for Chrome Manifest V3

const browserAPI = typeof browser !== 'undefined' ? browser : chrome;

// Set default settings on install
browserAPI.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    browserAPI.storage.sync.set({ apiUrl: 'http://localhost:8000' });
    console.log('[Background] Extension installed, defaults set');
  }
});

// Message handler (currently unused, popup handles everything)
browserAPI.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[Background] Message received:', request.action);
  return true;
});

console.log('[Background] Service worker loaded');

