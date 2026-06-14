"""
ai/priority.py — Priority scoring engine
"""

from utils import CATEGORY_BASE_WEIGHTS, CRITICAL_KEYWORDS, MULTI_VICTIM_KEYWORDS, NIGHT_PENALTY


class PriorityEngine:
    def __init__(self):
        self.base_weights = CATEGORY_BASE_WEIGHTS.copy()
        self.critical_keywords = CRITICAL_KEYWORDS
        self.multi_victim_keywords = MULTI_VICTIM_KEYWORDS
        self.night_penalty = NIGHT_PENALTY
    
    def score(self, category: str, description: str, confidence: float, time_of_day: str = "Day"):
        base = self.base_weights.get(category, 30)
        
        keyword_boost = 0
        desc_lower = description.lower()
        
        for lang in self.critical_keywords:
            for kw in self.critical_keywords[lang]:
                if kw in desc_lower:
                    keyword_boost += 5
        keyword_boost = min(keyword_boost, 25)
        
        victim_boost = 0
        for kw in self.multi_victim_keywords:
            if kw in desc_lower:
                victim_boost += 10
        victim_boost = min(victim_boost, 20)
        
        confidence_boost = int(confidence * 10)
        night_penalty = self.night_penalty if time_of_day == "Night" else 0
        
        score = base + keyword_boost + victim_boost + confidence_boost + night_penalty
        score = min(score, 100)
        
        if score >= 80:
            level = "Critical"
        elif score >= 60:
            level = "High"
        elif score >= 40:
            level = "Medium"
        else:
            level = "Low"
        
        return score, level
