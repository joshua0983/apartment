export class AmenitiesAnalyzer {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.radius = 500; // meters (approx 5-6 min walk)
    }

    async analyze(lat, lng) {
        // Run searches in parallel
        const categories = {
            restaurant: 'restaurant',
            cafe: 'cafe',
            bar: 'bar'
        };

        const results = {
            restaurants: 0,
            cafes: 0,
            bars: 0,
            bubble_tea: 0
        };

        const promises = [];

        // 1. Search for standard types
        for (const [key, type] of Object.entries(categories)) {
            promises.push(
                this.searchNearby(lat, lng, type, null).then(count => {
                    results[key + 's'] = count; // pluralize key
                })
            );
        }

        // 2. Search for Bubble Tea (keyword)
        promises.push(
            this.searchNearby(lat, lng, null, 'bubble tea').then(count => {
                results.bubble_tea = count;
            })
        );

        await Promise.all(promises);

        // Calculate totals and score
        const total = results.restaurants + results.cafes + results.bars + results.bubble_tea;
        
        // Simple density score (0-10)
        // 50+ places nearby = 10/10
        // 0 places = 0/10
        let score = Math.min(10, Math.ceil(total / 5));

        return {
            total_amenities: total,
            restaurants: results.restaurants,
            cafes: results.cafes,
            bars: results.bars,
            bubble_tea: results.bubble_tea,
            amenity_density_score: score
        };
    }

    async searchNearby(lat, lng, type, keyword) {
        let url = `https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=${lat},${lng}&radius=${this.radius}&key=${this.apiKey}`;
        
        if (type) {
            url += `&type=${type}`;
        }
        if (keyword) {
            url += `&keyword=${encodeURIComponent(keyword)}`;
        }

        try {
            const response = await fetch(url);
            const data = await response.json();

            if (data.status === 'OK' || data.status === 'ZERO_RESULTS') {
                return data.results.length;
            } else {
                console.error(`[Amenities] API Error for ${type || keyword}:`, data.status);
                return 0;
            }
        } catch (error) {
            console.error(`[Amenities] Fetch error for ${type || keyword}:`, error);
            return 0;
        }
    }
}
