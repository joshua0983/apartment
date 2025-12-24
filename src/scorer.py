"""
Score apartment listings based on all criteria
"""

from typing import Dict


class ApartmentScorer:
    """Calculate overall rating for apartment listings"""
    
    # Scoring weights (must sum to 1.0)
    WEIGHTS = {
        'commute': 0.40,
        'subway_proximity': 0.30,
        'amenities': 0.20,
        'requirements_bonus': 0.10,
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize scorer
        
        Args:
            weights: Custom scoring weights (optional)
        """
        if weights:
            self.weights = weights
        else:
            self.weights = self.WEIGHTS
    
    def calculate_score(
        self,
        meets_requirements: bool,
        commutes: Dict[str, Dict],
        subway_data: Dict,
        amenities_data: Dict
    ) -> Dict:
        """
        Calculate overall score out of 5.00
        
        Args:
            meets_requirements: Whether basic requirements are met
            commutes: Commute data for all offices
            subway_data: Nearest subway station data
            amenities_data: Activity area proximity data
            
        Returns:
            Dictionary with score and breakdown
        """
        if not meets_requirements:
            return {
                'score': 0.0,
                'breakdown': {
                    'requirements': 'FAILED',
                    'commute_score': 0.0,
                    'subway_score': 0.0,
                    'amenities_score': 0.0,
                },
                'explanation': 'Does not meet basic requirements'
            }
        
        # Calculate component scores (0-5 scale)
        commute_score = self._score_commute(commutes)
        subway_score = self._score_subway_proximity(subway_data)
        amenities_score = self._score_amenities(amenities_data)
        
        # Weighted total
        total_score = (
            commute_score * self.weights['commute'] +
            subway_score * self.weights['subway_proximity'] +
            amenities_score * self.weights['amenities']
        )
        
        # Normalize to 5.0 scale (currently weights sum to 0.9, reserve 0.1 for bonus)
        base_total = total_score / (1.0 - self.weights['requirements_bonus'])
        
        # Add bonus for meeting all preferences
        bonus = 0.0
        if self._meets_all_preferences(commutes, subway_data):
            bonus = 5.0 * self.weights['requirements_bonus']
        
        final_score = min(5.0, base_total + bonus)
        
        return {
            'score': round(final_score, 2),
            'breakdown': {
                'requirements': 'PASSED',
                'commute_score': round(commute_score, 2),
                'subway_score': round(subway_score, 2),
                'amenities_score': round(amenities_score, 2),
                'bonus': round(bonus, 2),
            },
            'explanation': self._generate_explanation(
                final_score, commute_score, subway_score, amenities_score
            )
        }
    
    def _score_commute(self, commutes: Dict[str, Dict]) -> float:
        """Score commute times (0-5 scale)"""
        # Find best (shortest) commute, filtering out None values
        valid_commutes = [
            c.get('duration_minutes') 
            for c in commutes.values() 
            if c.get('duration_minutes') is not None
        ]
        
        if not valid_commutes:
            return 0.0
        
        # Strict requirement: 5/5 only if ALL offices are < 30 mins
        max_commute = max(valid_commutes)
        if max_commute < 30:
            return 5.0
            
        # Otherwise score based on best commute, but cap at 4.0
        min_commute = min(valid_commutes)
        
        # Scoring: 5.0 for <20 min, 4.0 for 20-30, decreasing after 30
        if min_commute < 20:
            base_score = 5.0
        elif min_commute < 30:
            base_score = 4.0 - ((min_commute - 20) / 10) * 1.0
        elif min_commute < 45:
            base_score = 3.0 - ((min_commute - 30) / 15) * 2.0
        else:
            base_score = max(0.0, 1.0 - ((min_commute - 45) / 30))
            
        return min(4.0, base_score)
    
    def _score_subway_proximity(self, subway_data: Dict) -> float:
        """Score subway proximity (0-5 scale)"""
        walk_time = subway_data.get('walk_time_minutes')
        
        # Handle None or missing walk time
        if walk_time is None:
            return 0.0
        
        # Scoring: 5.0 for <5 min, decreasing linearly
        if walk_time < 5:
            return 5.0
        elif walk_time < 10:
            return 4.0 - ((walk_time - 5) / 5) * 1.5
        elif walk_time < 15:
            return 2.5 - ((walk_time - 10) / 5) * 1.5
        else:
            return max(0.0, 1.0 - ((walk_time - 15) / 10))
    
    def _score_amenities(self, amenities_data: Dict) -> float:
        """Score amenity proximity (0-5 scale)"""
        density_score = amenities_data.get('amenity_density_score', 0.0)
        
        # Handle None density score
        if density_score is None:
            density_score = 0.0
        
        # Convert 0-10 density to 0-5 scale
        density_component = (density_score / 10.0) * 5.0
        
        # For now, just return density component (we don't have walk time to amenities area)
        return density_component
    
    def _meets_all_preferences(
        self, 
        commutes: Dict[str, Dict], 
        subway_data: Dict
    ) -> bool:
        """Check if listing meets all preferences"""
        # Filter out None values from commute times
        valid_commutes = [
            c.get('duration_minutes')
            for c in commutes.values()
            if c.get('duration_minutes') is not None
        ]
        
        if not valid_commutes:
            return False
        
        worst_commute = max(valid_commutes)
        subway_walk = subway_data.get('walk_time_minutes')
        
        # Check if both preferences are met
        if subway_walk is None:
            return False
            
        return worst_commute < 30 and subway_walk < 5
    
    def _generate_explanation(
        self, 
        total: float,
        commute: float, 
        subway: float, 
        amenities: float
    ) -> str:
        """Generate human-readable explanation"""
        rating = "Excellent" if total >= 4.5 else \
                 "Great" if total >= 4.0 else \
                 "Good" if total >= 3.0 else \
                 "Fair" if total >= 2.0 else "Poor"
        
        return f"{rating} location with commute score {commute:.1f}/5, " \
               f"subway {subway:.1f}/5, amenities {amenities:.1f}/5"
