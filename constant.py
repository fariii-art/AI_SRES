"""
constants.py — Configuration constants for SERS
"""

# Emergency Categories
EMERGENCY_CATEGORIES = [
    "Fire",
    "Traffic Accident",
    "Crime",
    "Medical",
    "Flood",
    "Infrastructure"
]

# Category display names
CATEGORY_DISPLAY = {
    "Fire": "🔥 Fire",
    "Traffic Accident": "🚗 Traffic Accident",
    "Crime": "🔫 Crime",
    "Medical": "🏥 Medical",
    "Flood": "🌊 Flood",
    "Infrastructure": "🏗️ Infrastructure"
}

# Priority levels
PRIORITY_LEVELS = {
    "Critical": (80, 100),
    "High": (60, 79),
    "Medium": (40, 59),
    "Low": (0, 39)
}

# Base weights for each category (0-100 scale)
CATEGORY_BASE_WEIGHTS = {
    "Fire": 42,
    "Traffic Accident": 35,
    "Crime": 45,
    "Medical": 50,
    "Flood": 40,
    "Infrastructure": 30
}

# Critical keywords for priority boosting
CRITICAL_KEYWORDS = {
    "english": [
        "critical", "emergency", "urgent", "life threatening", "death",
        "unconscious", "bleeding heavily", "heart attack", "stroke",
        "fire spreading", "explosion", "hostage", "shooting"
    ],
    "urdu": [
        "ہنگامی", "شدید", "خون", "آگ", "دھماکہ", "فائرنگ",
        "بے ہوش", "دل کا دورہ", "جان لیوا"
    ],
    "roman": [
        "hungami", "shadeed", "khoon", "aag", "dhamaka", "firing",
        "be hosh", "dil ka dora", "jaan lewa"
    ]
}

# Multi-victim indicators
MULTI_VICTIM_KEYWORDS = [
    "multiple", "many", "several", "crowd", "大批", "بہت سے",
    "کئی", "10", "20", "30", "50", "100"
]

# Response speed (km/h) for ETA calculation
RESPONSE_SPEED_KPH = 60

# Night time penalty for priority
NIGHT_PENALTY = 15
NIGHT_START_HOUR = 20  # 8 PM
NIGHT_END_HOUR = 6     # 6 AM

# Model configuration
MODEL_CACHE_PATH = "sers_model.pkl"
DEFAULT_DATASET_SIZE = 100000
TEST_SIZE_RATIO = 0.15
TFIDF_MAX_FEATURES = 50000
TFIDF_NGRAM_RANGE = (2, 5)
LOGISTIC_C = 5.0

# Database configuration
DB_PATH = "sers.db"