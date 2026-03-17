// Main Evaluator class
import { CommuteCalculator } from './commute.js';
import { ProximityAnalyzer } from './proximity.js';
import { ApartmentScorer } from './scorer.js';
import { AmenitiesAnalyzer } from './amenities.js';

export class Evaluator {
    constructor(apiKey, offices) {
        this.apiKey = apiKey;
        this.commuteCalc = new CommuteCalculator(apiKey, offices);
        this.proximityAnalyzer = new ProximityAnalyzer();
        this.amenitiesAnalyzer = new AmenitiesAnalyzer(apiKey);
        this.scorer = new ApartmentScorer();
    }

    async evaluate(address) {
        console.log('[Evaluator] evaluating:', address);

        // 1. Geocode address using Google Maps Geocoding API
        const location = await this.geocode(address);
        if (!location) {
            throw new Error('Could not geocode address');
        }

        const { lat, lng, formatted_address } = location;

        // 2. Run analyses in parallel
        const [commutes, subway, amenities] = await Promise.all([
            this.commuteCalc.calculateCommutes(lat, lng),
            this.proximityAnalyzer.findNearestSubway(lat, lng),
            this.amenitiesAnalyzer.analyze(lat, lng)
        ]);

        // 3. Score
        const scoreResult = this.scorer.calculateScore(commutes, subway, amenities);

        return {
            address: address, // Input address
            input_address: formatted_address, // Formatted
            timestamp: new Date().toISOString(),
            coordinates: { lat, lng },
            commutes: commutes,
            subway: subway,
            amenities: amenities,
            score: scoreResult.score,
            breakdown: scoreResult.breakdown,
            explanation: scoreResult.explanation,
            cached: false
        };
    }

    async geocode(address) {
        const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${this.apiKey}`;
        const response = await fetch(url);
        const data = await response.json();

        if (data.status === 'OK' && data.results.length > 0) {
            const result = data.results[0];
            return {
                lat: result.geometry.location.lat,
                lng: result.geometry.location.lng,
                formatted_address: result.formatted_address
            };
        }
        console.error('[Evaluator] Geocode failed:', data.status);
        return null;
    }
}
