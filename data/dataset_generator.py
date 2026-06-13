"""
data/dataset_generator.py — Training dataset generator for SERS
================================================================
Generates a bilingual (English/Urdu) dataset of emergency reports
for training the classification model.

Features:
- 100,000 samples across 6 emergency categories
- 60% English, 40% Urdu split per category
- Geographic variation (20 cities × 30 area names)
- Linguistic noise (typos, Romanized Urdu)
- Urgency variation markers
"""

import random
import pandas as pd
import numpy as np
from pathlib import Path

# Set random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Emergency categories
CATEGORIES = [
    "Fire",
    "Traffic Accident", 
    "Crime",
    "Medical",
    "Flood",
    "Infrastructure"
]

# Cities for geographic variation
CITIES = [
    "Peshawar", "Islamabad", "Rawalpindi", "Lahore", "Faisalabad",
    "Multan", "Gujranwala", "Sialkot", "Quetta", "Karachi",
    "Hyderabad", "Sukkur", "Mardan", "Abbottabad", "Bahawalpur",
    "Sargodha", "Sheikhupura", "Jhang", "Dera Ghazi Khan", "Rahim Yar Khan"
]

# Area names for location variation
AREAS = [
    "Main Bazaar", "Cantt", "Defence", "Gulberg", "Johar Town",
    "Saddar", "University Road", "GT Road", "Industrial Area",
    "City Center", "Phase 1", "Phase 2", "Ring Road", "Airport Road",
    "Railway Station", "Bus Terminal", "Hospital Road", "Police Station Area"
]

# ==================== TEMPLATES BY CATEGORY ====================

FIRE_TEMPLATES_EN = [
    "{urgency} {area} {city} mein aag lag gai hai. Building mein intense blaze hai.",
    "Fire at {area}, {city}. Building is on fire. {urgency} help needed!",
    "{area} mein dukaan mein aag lag gai. {urgency} fire brigade bhejein.",
    "Major fire at {area} {city}. Multiple buildings affected. {urgency}",
    "{area} petrol pump mein explosion hua hai. Aag phail rahi hai. {urgency}",
    "Chemical factory fire at {area} {city}. Toxic smoke spreading. {urgency}",
    "Wildfire near {area} residential area. {urgency} fire response needed.",
    "Electric short circuit caused fire at {area} apartment building. {urgency}",
    "Kitchen gas cylinder explosion at {area} {city}. {urgency} fire rescue needed.",
    "Forest fire spreading towards {area} settlements. {urgency} disaster response."
]

FIRE_TEMPLATES_UR = [
    "{urgency} {area} {city} میں آگ لگ گئی ہے۔ عمارت میں شدید آگ ہے۔",
    "{area} {city} میں فائر۔ عمارت جل رہی ہے۔ {urgency} مدد کی ضرورت ہے۔",
    "{area} میں دکان میں آگ لگی۔ {urgency} فائر بریگیڈ بھیجیں۔",
    "{area} {city} میں بڑی آگ۔ متعدد عمارتیں متاثر۔ {urgency}",
    "{area} پیٹرول پمپ پر دھماکہ۔ آگ پھیل رہی ہے۔ {urgency}",
    "{area} میں کیمیکل فیکٹری میں آگ۔ زہریلا دھواں پھیل رہا ہے۔ {urgency}",
]

TRAFFIC_TEMPLATES_EN = [
    "{urgency} accident at {area} {city}. Multiple vehicles involved. Injuries reported.",
    "Car collision on {area}, {city}. People trapped inside. {urgency} ambulance needed.",
    "Major pileup on {area} {city} due to fog. {urgency} traffic police and rescue.",
    "Truck overturned at {area} {city}. Road completely blocked. {urgency}",
    "Hit and run at {area} {city}. Pedestrian critically injured. {urgency}",
    "Motorcycle accident at {area} {city}. Rider unconscious. {urgency} medical help.",
    "Bus collided with car at {area} {city}. Multiple passengers injured. {urgency}",
    "Accident at {area} intersection. Traffic jam for kilometers. {urgency} police needed.",
    "Vehicle fell into ravine at {area} {city}. {urgency} rescue and medical teams.",
    "Pedestrian struck by speeding car at {area} crossing. {urgency} ambulance."
]

TRAFFIC_TEMPLATES_UR = [
    "{urgency} {area} {city} میں حادثہ۔ متعدد گاڑیاں شامل۔ زخمی ہیں۔",
    "{area} {city} پر گاڑیوں کا تصادم۔ لوگ پھنس گئے ہیں۔ {urgency} ایمبولینس چاہیے۔",
    "{area} {city} پر دھند کی وجہ سے بڑا حادثہ۔ {urgency} ٹریفک پولیس چاہیے۔",
    "{area} {city} پر ٹرک الٹ گیا۔ سڑک مکمل بلاک۔ {urgency}",
    "{area} {city} پر ہٹ اینڈ رن۔ پیدل چلنے والا شدید زخمی۔ {urgency}",
]

CRIME_TEMPLATES_EN = [
    "{urgency} robbery in progress at {area} {city}. Armed suspects. Police needed immediately.",
    "Shots fired at {area} {city}. {urgency} police and ambulance required.",
    "House break-in at {area} {city}. Family trapped inside. {urgency} police response.",
    "Street mugging at {area} {city}. Victim stabbed. {urgency} medical and police.",
    "Carjacking at gunpoint on {area} {city}. Suspects fleeing. {urgency}",
    "Domestic violence incident at {area} {city}. Weapons involved. {urgency} police.",
    "Kidnapping reported at {area} {city}. Child taken. {urgency} search teams needed.",
    "Bank robbery at {area} {city}. Hostages inside. {urgency} tactical response.",
    "Gang violence in {area} {city}. Multiple shots heard. {urgency} police backup.",
    "Harassment incident at {area} {city}. Suspect still at large. {urgency} police."
]

CRIME_TEMPLATES_UR = [
    "{urgency} {area} {city} میں ڈکیتی جاری۔ مسلح ملزمان۔ پولیس فوری چاہیے۔",
    "{area} {city} میں فائرنگ۔ {urgency} پولیس اور ایمبولینس چاہیے۔",
    "{area} {city} میں گھر میں چوری۔ فیملی پھنس گئی۔ {urgency} پولیس چاہیے۔",
    "{area} {city} میں اسٹریٹ ڈکیتی۔ شہید زخمی۔ {urgency} طبی امداد چاہیے۔",
    "{area} {city} پر بندوق کے زور پر گاڑی چھینی۔ ملزمان فرار۔ {urgency}",
]

MEDICAL_TEMPLATES_EN = [
    "{urgency} heart attack at {area} {city}. Patient unconscious. Ambulance needed immediately.",
    "Person collapsed at {area} {city}. Not breathing. {urgency} paramedics required.",
    "Severe bleeding from accident at {area} {city}. {urgency} ambulance and trauma care.",
    "Stroke symptoms at {area} {city}. Elderly patient. {urgency} medical emergency.",
    "Child having seizure at {area} {city}. {urgency} ambulance and pediatric care.",
    "Pregnant woman in labor at {area} {city}. Complications developing. {urgency} ambulance.",
    "Burn injuries from fire at {area} {city}. Critical condition. {urgency} medical help.",
    "Allergic reaction at {area} {city}. Throat swelling. {urgency} epinephrine needed.",
    "Diabetic emergency at {area} {city}. Patient unconscious. {urgency} paramedics.",
    "Drug overdose at {area} {city}. Breathing shallow. {urgency} medical intervention."
]

MEDICAL_TEMPLATES_UR = [
    "{urgency} {area} {city} میں ہارٹ اٹیک۔ مریض بے ہوش۔ فوری ایمبولینس چاہیے۔",
    "{area} {city} میں شخص گر گیا۔ سانس نہیں آرہی۔ {urgency} پیرامیڈیکس چاہیے۔",
    "{area} {city} میں حادثے سے شدید خون بہہ رہا۔ {urgency} ایمبولینس چاہیے۔",
    "{area} {city} میں اسٹروک کی علامات۔ بوڑھا مریض۔ {urgency} طبی ایمرجنسی۔",
    "{area} {city} میں بچے کو دورے پڑ رہے ہیں۔ {urgency} ایمبولینس چاہیے۔",
]

FLOOD_TEMPLATES_EN = [
    "{urgency} flash flood at {area} {city}. Water entering homes. Rescue teams needed.",
    "People trapped on roof at {area} {city}. Rising water levels. {urgency} boat rescue.",
    "Urban flooding at {area} {city}. Streets submerged. {urgency} evacuation needed.",
    "Dam overflow warning at {area} {city}. {urgency} downstream evacuation required.",
    "Heavy rains causing flooding at {area} {city}. Families stranded in vehicles. {urgency}",
    "River overflow at {area} {city}. Bridge collapsed. {urgency} rescue operations.",
    "Landslide blocking road at {area} {city}. People trapped. {urgency} disaster response.",
    "Flood water entering hospital at {area} {city}. Patient evacuation needed. {urgency}",
    "Village cut off by floods at {area} {city}. Food and medical supplies needed. {urgency}",
    "Water level rising rapidly at {area} {city}. {urgency} immediate rescue required."
]

FLOOD_TEMPLATES_UR = [
    "{urgency} {area} {city} میں اچانک سیلاب۔ گھروں میں پانی۔ ریسکیو ٹیمیں چاہیے۔",
    "{area} {city} میں لوگ چھت پر پھنس گئے۔ پانی بڑھ رہا ہے۔ {urgency} کشتی ریسکیو چاہیے۔",
    "{area} {city} میں شہری سیلاب۔ سڑکیں ڈوب گئیں۔ {urgency} انخلاء چاہیے۔",
    "{area} {city} میں ڈیم اوور فلو کی وارننگ۔ {urgency} نیچے والے علاقوں کو خالی کروانا۔",
    "{area} {city} میں تیز بارشوں سے سیلاب۔ فیملیز گاڑیوں میں پھنس گئیں۔ {urgency}",
]

INFRASTRUCTURE_TEMPLATES_EN = [
    "{urgency} building collapse at {area} {city}. People trapped under debris. Rescue needed.",
    "Gas leak at {area} {city}. Strong odor. {urgency} evacuate area. Fire department needed.",
    "Live wire down at {area} {city}. Electrocution risk. {urgency} power company and rescue.",
    "Bridge collapse at {area} {city}. Vehicles in water. {urgency} multi-agency response.",
    "Sewage pipe burst at {area} {city}. Raw sewage flooding streets. {urgency} civic works.",
    "Crane collapse at construction site {area} {city}. Worker injured. {urgency} rescue.",
    "Power pole falling at {area} {city}. Blocking road and electrified. {urgency}",
    "Water pipeline burst at {area} {city}. Flooding basements. {urgency} water department.",
    "Road sinkhole at {area} {city}. Vehicle swallowed. {urgency} rescue and traffic control.",
    "Factory chemical leak at {area} {city}. Evacuation needed. {urgency} hazmat teams."
]

INFRASTRUCTURE_TEMPLATES_UR = [
    "{urgency} {area} {city} میں عمارت گر گئی۔ لوگ ملبے تلے دب گئے۔ ریسکیو چاہیے۔",
    "{area} {city} میں گیس کا رساو۔ تیز بدبو۔ {urgency} علاقہ خالی کروائیں۔",
    "{area} {city} میں تار ٹوٹ گئی۔ بجلی کا جھٹکا لگنے کا خطرہ۔ {urgency} بجلی کمپنی چاہیے۔",
    "{area} {city} میں پل گر گیا۔ گاڑیاں پانی میں۔ {urgency} فوری ریسکیو۔",
    "{area} {city} میں سیوریج پائپ پھٹ گیا۔ گلیوں میں گندا پانی۔ {urgency} میونسپلٹی چاہیے۔",
]

# Urgency markers
URGENCY_MARKERS = {
    "High": ["IMPORTANT", "URGENT", "EMERGENCY", "CRITICAL", "HELP FAST"],
    "Medium": ["Please", "Request", "Need help", "Assistance required"],
    "Low": ["Inquiry", "Query", "I think", "There might be"]
}

# Romanized Urdu variations
ROMANIZED_VARIATIONS = {
    "aag": "aag",
    "fire": "phire",
    "accident": "aksident",
    "police": "polees",
    "ambulance": "ambulens",
    "medical": "medikal",
    "flood": "flud",
    "building": "bilding",
    "road": "rod",
    "help": "help",
    "madad": "madad",
    "emergency": "emargency",
}


def apply_linguistic_noise(text: str, category: str) -> str:
    """Apply linguistic noise to simulate real-world input."""
    words = text.split()
    
    # 20% chance of common typos
    if random.random() < 0.2:
        # Swap two random characters in a word
        if words:
            idx = random.randint(0, len(words) - 1)
            if len(words[idx]) > 3:
                pos = random.randint(0, len(words[idx]) - 2)
                words[idx] = words[idx][:pos] + words[idx][pos+1] + words[idx][pos] + words[idx][pos+2:]
    
    # 15% chance to Romanize (if text is Urdu script)
    if random.random() < 0.15 and any('\u0600' <= c <= '\u06FF' for c in text):
        # Simplified romanization for demo - in real system would be more sophisticated
        roman_map = {
            'آگ': 'aag',
            'مدد': 'madad',
            'پولیس': 'police',
            'ایمبولینس': 'ambulance',
            'حادثہ': 'accident',
        }
        for urdu, roman in roman_map.items():
            if urdu in text:
                text = text.replace(urdu, roman)
        return text
    
    return ' '.join(words)


def generate_sample(category: str, include_urgency: bool = True) -> dict:
    """Generate a single training sample."""
    # Choose language (60% English, 40% Urdu)
    is_english = random.random() < 0.6
    
    # Select appropriate template pool
    if category == "Fire":
        templates = FIRE_TEMPLATES_EN if is_english else FIRE_TEMPLATES_UR
    elif category == "Traffic Accident":
        templates = TRAFFIC_TEMPLATES_EN if is_english else TRAFFIC_TEMPLATES_UR
    elif category == "Crime":
        templates = CRIME_TEMPLATES_EN if is_english else CRIME_TEMPLATES_UR
    elif category == "Medical":
        templates = MEDICAL_TEMPLATES_EN if is_english else MEDICAL_TEMPLATES_UR
    elif category == "Flood":
        templates = FLOOD_TEMPLATES_EN if is_english else FLOOD_TEMPLATES_UR
    else:  # Infrastructure
        templates = INFRASTRUCTURE_TEMPLATES_EN if is_english else INFRASTRUCTURE_TEMPLATES_UR
    
    # Select random template
    template = random.choice(templates)
    
    # Select random city and area
    city = random.choice(CITIES)
    area = random.choice(AREAS)
    
    # Format template
    text = template.format(
        area=area,
        city=city,
        urgency="URGENT" if include_urgency and random.random() < 0.7 else ""
    )
    
    # Clean up extra spaces
    text = ' '.join(text.split())
    
    # Apply linguistic noise
    text = apply_linguistic_noise(text, category)
    
    return {
        "text": text,
        "label": category,
        "city": city,
        "area": area,
        "is_english": is_english
    }


def get_training_data(size: int = 100000) -> pd.DataFrame:
    """
    Generate training dataset with specified number of samples.
    
    Parameters
    ----------
    size : int — total number of samples to generate
    
    Returns
    -------
    df : pd.DataFrame — dataset with 'text' and 'label' columns
    """
    samples_per_category = size // len(CATEGORIES)
    all_samples = []
    
    print(f"Generating {size:,} training samples...")
    
    for category in CATEGORIES:
        print(f"  Generating {samples_per_category:,} samples for {category}...")
        for _ in range(samples_per_category):
            sample = generate_sample(category)
            all_samples.append(sample)
    
    # Fill remaining samples if size not perfectly divisible
    remaining = size - len(all_samples)
    if remaining > 0:
        for _ in range(remaining):
            category = random.choice(CATEGORIES)
            sample = generate_sample(category)
            all_samples.append(sample)
    
    # Shuffle the dataset
    random.shuffle(all_samples)
    
    # Create DataFrame
    df = pd.DataFrame(all_samples)
    
    print(f"Dataset generated: {len(df):,} samples")
    print("\nClass distribution:")
    print(df['label'].value_counts())
    
    return df[['text', 'label']]


if __name__ == "__main__":
    # Generate and save dataset when run directly
    df = get_training_data(100000)
    
    # Save to CSV
    data_dir = Path(__file__).parent
    csv_path = data_dir / "sers_dataset.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"\nDataset saved to: {csv_path}")
    
    # Show sample
    print("\nSample entries:")
    print(df.head(10))