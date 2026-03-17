// Score apartment listings based on all criteria
// Reimplementation of src/scorer.py

export class ApartmentScorer {
    constructor() {
        this.weights = {
            commute: 0.40,
            subway: 0.30,
            amenities: 0.20,
            bonus: 0.10
        };
    }

    calculateScore(commutes, subwayData, amenitiesData) {
        // 1. Commute Score (0-5)
        const commuteScore = this.scoreCommute(commutes);

        // 2. Subway Score (0-5)
        const subwayScore = this.scoreSubway(subwayData);

        // 3. Amenities Score (0-5)
        // Note: Amenities data might be empty if we don't have Places API yet
        // For now, let's assume if it's missing, we score based on what we have
        const amenitiesScore = this.scoreAmenities(amenitiesData);

        // Calculate weighted score
        // Only sum weights for available data
        let totalWeight = this.weights.commute + this.weights.subway; // + this.weights.amenities;
        if (amenitiesData) totalWeight += this.weights.amenities;

        let totalScore = (commuteScore * this.weights.commute) + (subwayScore * this.weights.subway);
        if (amenitiesData) totalScore += (amenitiesScore * this.weights.amenities);

        // Normalize
        let finalScore = totalScore / totalWeight;

        // Bonus if everything is great
        let bonus = 0;
        if (commuteScore >= 4 && subwayScore >= 4) {
            bonus = 0.5; // Bonus 0.5
        }

        finalScore = Math.min(5.0, finalScore + bonus);

        return {
            score: parseFloat(finalScore.toFixed(2)),
            breakdown: {
                commute_score: parseFloat(commuteScore.toFixed(2)),
                subway_score: parseFloat(subwayScore.toFixed(2)),
                amenities_score: parseFloat(amenitiesScore.toFixed(2)),
                bonus: bonus
            },
            explanation: `Commute: ${commuteScore.toFixed(1)}/5, Subway: ${subwayScore.toFixed(1)}/5`
        };
    }

    scoreCommute(commutes) {
        // Find best and worst commutes
        let minDuration = Infinity;
        let maxDuration = -Infinity;
        let validCommutes = 0;

        for (const key in commutes) {
            const c = commutes[key];
            if (c && c.duration_minutes !== undefined) {
                const duration = c.duration_minutes;
                if (duration < minDuration) minDuration = duration;
                if (duration > maxDuration) maxDuration = duration;
                validCommutes++;
            }
        }

        if (validCommutes === 0) return 0;

        // Python Logic: Strict requirement: 5/5 only if ALL offices are < 30 mins
        // If we have multiple offices configured, apply this strict rule.
        // If only 1 office execution, max === min so it works too.
        if (maxDuration < 30) {
            return 5.0;
        }

        // Otherwise score based on best commute to ANY office, but capped at 4.0
        // Scoring: 
        // < 20 mins: 5.0 (but capped at 4.0 here) -> 4.0
        // 20-30 mins: 4.0
        // 30-45 mins: 3.0
        // ...
        
        let baseScore = 0;
        if (minDuration < 20) {
            baseScore = 5.0;
        } else if (minDuration < 30) {
            baseScore = 4.0 - ((minDuration - 20) / 10) * 1.0;
        } else if (minDuration < 45) {
            baseScore = 3.0 - ((minDuration - 30) / 15) * 2.0;
        } else {
            baseScore = Math.max(0.0, 1.0 - ((minDuration - 45) / 30));
        }

        return Math.min(4.0, baseScore);
    }

    scoreSubway(subwayData) {
        if (!subwayData || !subwayData.walk_time_minutes) return 0;

        const minutes = subwayData.walk_time_minutes;
        
        // < 3 mins: 5.0
        // 3-5 mins: 4.5
        // 5-8 mins: 4.0
        // 8-12 mins: 3.0
        // 12-15 mins: 2.0
        // > 15 mins: 1.0
        if (minutes < 3) return 5.0;
        if (minutes <= 5) return 4.5;
        if (minutes <= 8) return 4.0;
        if (minutes <= 12) return 3.0;
        if (minutes <= 15) return 2.0;
        return 1.0;
    }

    scoreAmenities(amenities) {
        if (!amenities || typeof amenities.amenity_density_score !== 'number') {
            return 0;
        }
        
        // Scale 0-10 density score to 0-5
        return (amenities.amenity_density_score / 10.0) * 5.0;
    }
}
