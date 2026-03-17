// Commute calculator using Google Maps Distance Matrix API
// Reimplementation of src/commute.py

export class CommuteCalculator {
    constructor(apiKey, offices) {
        this.apiKey = apiKey;
        this.offices = offices || [
            { id: 'office_1', name: 'Office 1 (Midtown East)', address: '110 E 59th St, New York, NY 10022' },
            { id: 'office_2', name: 'Office 2 (Midtown)', address: '767 5th Ave, New York, NY 10153' },
            { id: 'office_3', name: 'Office 3 (SoHo)', address: '130 Prince St, New York, NY 10012' },
            { id: 'office_4', name: 'Office 4 (Chelsea)', address: '40 W 23rd St, New York, NY 10010' }
        ];
    }

    async calculateCommutes(originLat, originLng) {
        // Calculate arrival time: Next weekday at 9 AM
        const arrivalTime = this.getNextWeekday9AM();
        const originStr = `${originLat},${originLng}`;
        const results = {};

        // We can batch destinations to save API calls
        // Max 25 destinations per call, we have ~4.
        const destinations = this.offices.map(o => o.address).join('|');

        const url = `https://maps.googleapis.com/maps/api/distancematrix/json?origins=${originStr}&destinations=${encodeURIComponent(destinations)}&mode=transit&arrival_time=${arrivalTime}&units=imperial&key=${this.apiKey}`;

        try {
            const response = await fetch(url);
            const data = await response.json();

            if (data.status !== 'OK') {
                console.error('[Commute] API Error:', data.status, data.error_message);
                throw new Error(data.error_message || 'API Error');
            }

            const elements = data.rows[0].elements;

            this.offices.forEach((office, index) => {
                const element = elements[index];
                if (element.status === 'OK') {
                    const durationText = element.duration.text;
                    const durationValue = element.duration.value; // seconds
                    const durationMinutes = Math.round(durationValue / 60);

                    results[office.name] = {
                        destination: office.address,
                        duration_text: durationText,
                        duration_minutes: durationMinutes,
                        distance_text: element.distance.text,
                        mode: 'transit',
                        meets_preference: durationMinutes <= 45 // Hardcoded 45 min preference
                    };
                } else {
                    results[office.name] = {
                        error: element.status,
                        meets_preference: false
                    };
                }
            });

        } catch (error) {
            console.error('[Commute] Fetch error:', error);
            // Return empty or error for all
            this.offices.forEach(office => {
                results[office.name] = { error: error.message };
            });
        }

        return results;
    }

    getNextWeekday9AM() {
        const d = new Date();
        // Add 1 day
        d.setDate(d.getDate() + 1);
        // While Sat (6) or Sun (0), add 1 day
        while (d.getDay() === 0 || d.getDay() === 6) {
            d.setDate(d.getDate() + 1);
        }
        d.setHours(9, 0, 0, 0);
        return Math.floor(d.getTime() / 1000); // Unix timestamp in seconds
    }
}
