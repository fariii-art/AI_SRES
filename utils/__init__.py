"""
Utils package for SERS - Configuration constants
"""

# Emergency Categories
EMERGENCY_CATEGORIES = [
    "Fire",
    "Accident",
    "Medical",
    "Crime",
    "Flood",
    "Earthquake"
]

# Category display names
CATEGORY_DISPLAY = {
    "Fire": "🔥 Fire",
    "Accident": "🚗 Accident",
    "Medical": "🏥 Medical",
    "Crime": "🔫 Crime",
    "Flood": "🌊 Flood",
    "Earthquake": "🌋 Earthquake"
}

# Priority levels
PRIORITY_LEVELS = {
    "Critical": (80, 100),
    "High": (60, 79),
    "Medium": (40, 59),
    "Low": (0, 39)
}

# Base weights for categories
CATEGORY_BASE_WEIGHTS = {
    "Fire": 42,
    "Accident": 35,
    "Medical": 50,
    "Crime": 45,
    "Flood": 40,
    "Earthquake": 48
}

# Critical keywords
CRITICAL_KEYWORDS = {
    "english": ["critical", "emergency", "urgent", "heart attack", "fire", "shooting", "bleeding"],
    "urdu": ["ہنگامی", "شدید", "خون", "آگ", "دھماکہ", "فائرنگ"],
    "roman": ["hungami", "shadeed", "khoon", "aag", "dhamaka", "firing"]
}

# Multi-victim indicators
MULTI_VICTIM_KEYWORDS = ["multiple", "many", "several", "crowd"]

# Response speed (km/h)
RESPONSE_SPEED_KPH = 70

# Night penalty
NIGHT_PENALTY = 15
NIGHT_START_HOUR = 20
NIGHT_END_HOUR = 6

# Model configuration
MODEL_CACHE_PATH = "sers_model.pkl"
DEFAULT_DATASET_SIZE = 5000
TEST_SIZE_RATIO = 0.15
TFIDF_MAX_FEATURES = 5000
TFIDF_NGRAM_RANGE = (2, 5)
LOGISTIC_C = 1.0

# Database
DB_PATH = "sers.db"

# Export list
__all__ = [
    'EMERGENCY_CATEGORIES',
    'CATEGORY_DISPLAY',
    'PRIORITY_LEVELS',
    'CATEGORY_BASE_WEIGHTS',
    'CRITICAL_KEYWORDS',
    'MULTI_VICTIM_KEYWORDS',
    'RESPONSE_SPEED_KPH',
    'NIGHT_PENALTY',
    'NIGHT_START_HOUR',
    'NIGHT_END_HOUR',
    'MODEL_CACHE_PATH',
    'DEFAULT_DATASET_SIZE',
    'TEST_SIZE_RATIO',
    'TFIDF_MAX_FEATURES',
    'TFIDF_NGRAM_RANGE',
    'LOGISTIC_C',
    'DB_PATH'
]
