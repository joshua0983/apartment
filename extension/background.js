import { Evaluator } from './lib/evaluator.js';

// Open options on install
chrome.runtime.onInstalled.addListener((details) => {
    if (details.reason === 'install') {
        if (chrome.runtime.openOptionsPage) {
            chrome.runtime.openOptionsPage();
        } else {
            window.open(chrome.runtime.getURL('options.html'));
        }
    }
});

// Setup listener
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'evaluateAddress') {
        const { address } = request;
        
        chrome.storage.sync.get(['googleApiKey', 'officeLocations'], (storage) => {
            const apiKey = storage.googleApiKey;
            const offices = storage.officeLocations;

            if (!apiKey) {
                sendResponse({ error: 'No API Key configured. Please go to Extension Options to set it up.' });
                return;
            }

            const evaluator = new Evaluator(apiKey, offices);
            evaluator.evaluate(address)
                .then(result => {
                    sendResponse(result);
                })
                .catch(error => {
                    console.error('Evaluation failed:', error);
                    sendResponse({ error: error.message });
                });
        });
        
        return true; // Keep channel open for async response
    }
});

