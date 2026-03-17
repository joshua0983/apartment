// Saves options to chrome.storage
function saveOptions() {
    var apiKey = document.getElementById('apiKey').value;
    var officesText = document.getElementById('offices').value;
    
    let offices = [];
    try {
        offices = JSON.parse(officesText);
    } catch (e) {
        document.getElementById('status').textContent = 'Invalid JSON for offices.';
        document.getElementById('status').style.color = 'red';
        return;
    }
  
    chrome.storage.sync.set({
      googleApiKey: apiKey,
      officeLocations: offices
    }, function() {
      // Update status to let user know options were saved.
      var status = document.getElementById('status');
      status.textContent = 'Options saved.';
      status.style.color = 'green';
      setTimeout(function() {
        status.textContent = '';
      }, 750);
    });
  }
  
  // Restores select box and checkbox state using the preferences
  // stored in chrome.storage.
  function restoreOptions() {
    chrome.storage.sync.get({
      googleApiKey: '',
      officeLocations: [
        { name: 'Office 1 (Midtown East)', address: '110 E 59th St, New York, NY 10022' },
        { name: 'Office 2 (Midtown)', address: '767 5th Ave, New York, NY 10153' },
        { name: 'Office 3 (SoHo)', address: '130 Prince St, New York, NY 10012' },
        { name: 'Office 4 (Chelsea)', address: '40 W 23rd St, New York, NY 10010' }
      ]
    }, function(items) {
      document.getElementById('apiKey').value = items.googleApiKey;
      document.getElementById('offices').value = JSON.stringify(items.officeLocations, null, 2);
    });
  }
  
  document.addEventListener('DOMContentLoaded', restoreOptions);
  document.getElementById('save').addEventListener('click', saveOptions);
