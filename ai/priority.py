"""
ai/priority.py — Priority scoring engine
"""

import re


class PriorityEngine:
    """Calculate emergency priority scores (0-100)"""
    
    BASE_WEIGHTS = {
        "Fire": 42,
        "Accident": 35,
        "Medical": 50,
        "Crime": 45,
        "Flood": 40,
        "Earthquake": 48
    }
    
    CRITICAL_KEYWORDS = [
        "critical", "emergency", "urgent", "life threatening", "death",
        "unconscious", "bleeding", "heart attack", "stroke", "explosion",
        "shooting", "hostage", "آگ", "خون", "دھماکہ", "فائرنگ", "بے ہوش"
    ]
    
    MULTI_VICTIM = ["multiple", "many", "several", "crowd", "10", "20", "30"]
    NIGHT_PENALTY = 15
    
    def score(self, category: str, description: str, confidence: float, time_of_day: str = "Day") -> tuple:
        """Calculate priority score and level"""
        
        # Base score
        base = self.BASE_WEIGHTS.get(category, 30)
        
        # Critical keyword boost
        keyword_boost = 0
        desc_lower = description.lower()
        for kw in self.CRITICAL_KEYWORDS:
            if kw in desc_lower:
                keyword_boost += 5
        keyword_boost = min(keyword_boost, 25)
        
        # Multi-victim boost
        victim_boost = 0
        for kw in self.MULTI_VICTIM:
            if kw in desc_lower:
                victim_boost += 10
        victim_boost = min(victim_boost, 20)
        
        # Confidence boost
        confidence_boost = int(confidence * 10)
        
        # Night penalty
        night_penalty = self.NIGHT_PENALTY if time_of_day == "Night" else 0
        
        # Calculate final score
        score = base + keyword_boost + victim_boost + confidence_boost + night_penalty
        score = min(score, 100)
        
        # Determine level
        if score >= 80:
            level = "Critical"
        elif score >= 60:
            level = "High"
        elif score >= 40:
            level = "Medium"
        else:
            level = "Low"
        
        return score, level