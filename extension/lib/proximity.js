// Calculate proximity to subway stations
// Reimplementation of src/proximity.py

// Haversine formula to calculate distance between two points
function getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2) {
  var R = 6371; // Radius of the earth in km
  var dLat = deg2rad(lat2 - lat1); // deg2rad below
  var dLon = deg2rad(lon2 - lon1);
  var a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  var d = R * c; // Distance in km
  return d;
}

function deg2rad(deg) {
  return deg * (Math.PI / 180);
}

function kmToMiles(km) {
  return km * 0.621371;
}

// Calculate walking time (assuming 3 mph walking speed)
function calculateWalkTime(miles) {
    // 3 mph = 20 mins per mile
    // Add 2 mins for traffic/waiting
    return (miles * 20) + 2;
}

export class ProximityAnalyzer {
    constructor() {
        this.stations = null;
    }

    async loadStations() {
        if (this.stations) return;
        try {
            const url = chrome.runtime.getURL('data/subway_stations.json');
            const response = await fetch(url);
            this.stations = await response.json();
            console.log('[Proximity] Loaded', this.stations.length, 'stations');
        } catch (error) {
            console.error('[Proximity] Failed to load stations:', error);
            this.stations = [];
        }
    }

    async findNearestSubway(lat, lng) {
        if (!this.stations) await this.loadStations();

        if (!this.stations || this.stations.length === 0) {
            return {
                station_name: null,
                distance_miles: null,
                walk_time_minutes: null,
                lines: [],
                meets_preference: false,
                error: 'Subway data not loaded'
            };
        }

        let nearestStation = null;
        let minDistance = Infinity;

        for (const station of this.stations) {
            // Data has latitude/longitude
            const dKm = getDistanceFromLatLonInKm(lat, lng, station.latitude, station.longitude);
            const dMiles = kmToMiles(dKm);

            if (dMiles < minDistance) {
                minDistance = dMiles;
                nearestStation = station;
            }
        }

        if (nearestStation) {
            const walkTime = calculateWalkTime(minDistance);
            return {
                station_name: nearestStation.name,
                distance_miles: parseFloat(minDistance.toFixed(2)),
                walk_time_minutes: Math.round(walkTime),
                lines: nearestStation.lines,
                meets_preference: walkTime < 10 // Preference: 10 mins
            };
        }

        return {
            station_name: null,
            distance_miles: null,
            walk_time_minutes: null,
            lines: [],
            meets_preference: false
        };
    }
}
