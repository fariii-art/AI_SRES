"""
data/generate_training_data.py – Generate a 10,000-sample bilingual training set for SERS
"""

import os
import random
import pandas as pd

# Set random seed for reproducibility
random.seed(42)

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

CATEGORIES = ["Fire", "Accident", "Medical", "Crime", "Flood", "Earthquake"]

PHRASES = {
    "Fire": {
        "en": ["fire in building", "blaze at market", "smoke detected", "house on fire", "wildfire spreading"],
        "ur": ["آگ لگ گئی", "عمارت میں آگ", "دھواں اٹھ رہا", "گھر جل رہا", "جنگل میں آگ"],
        "mixed": ["aag lagi hai building mein", "smoke aa raha hai", "fire bohot tez hai"],
    },
    "Accident": {
        "en": ["car crash", "road accident", "vehicle collision", "truck overturned", "multiple vehicles"],
        "ur": ["کار حادثہ", "سڑک حادثہ", "ٹکر", "ٹرک الٹ گئی", "گاڑیاں ٹکرائیں"],
        "mixed": ["car ne truck ko hit kiya", "accident ho gaya highway par", "bohot zakhmi"],
    },
    "Medical": {
        "en": ["heart attack", "unconscious person", "bleeding severe", "stroke symptoms", "difficulty breathing"],
        "ur": ["دل کا دورہ", "بے ہوش شخص", "شدید خون بہہ رہا", "سانس لینے میں دشواری"],
        "mixed": ["heart attack aa raha hai", "bleeding band nahi ho rahi", "patient unconscious hai"],
    },
    "Crime": {
        "en": ["robbery in progress", "armed assault", "theft reported", "shooting heard", "break-in"],
        "ur": ["ڈکیتی ہو رہی", "چوری", "فائرنگ", "گھر میں توڑ پھوڑ"],
        "mixed": ["chor ghus gaye", "gunshot ki awaaz", "robbery ho gayi"],
    },
    "Flood": {
        "en": ["flood in area", "water rising", "river overflowing", "homes submerged", "heavy rain flooding"],
        "ur": ["سیلاب آ گیا", "پانی بڑھ رہا", "دریا کا بہاؤ", "گھر ڈوب گئے"],
        "mixed": ["paani har jagah hai", "flood bohot severe hai", "logon ko bachao"],
    },
    "Earthquake": {
        "en": ["earthquake felt", "ground shaking", "buildings swaying", "tremor strong", "after shocks"],
        "ur": ["زلزلہ محسوس ہوا", "زمین ہل رہی", "عمارتیں لہرا رہیں", "شدید جھٹکے"],
        "mixed": ["earthquake aa gaya", "zameen hil rahi hai", "building gir rahi"],
    },
}


def generate_row(category: str):
    """Generate a single training row"""
    lang = random.choice(["en", "ur", "mixed"])
    text = random.choice(PHRASES[category][lang])
    
    # Add urgency marker (20% chance)
    if random.random() < 0.2:
        text = f"help! {text} emergency"
    
    return text, category


def generate_dataset(num_samples: int = 10000) -> pd.DataFrame:
    """Generate dataset with specified number of samples"""
    rows = []
    
    for _ in range(num_samples):
        cat = random.choice(CATEGORIES)
        text, label = generate_row(cat)
        rows.append({"text": text, "label": label})
    
    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 50)
    print("SERS Training Data Generator")
    print("=" * 50)
    
    # Generate dataset
    df = generate_dataset(10000)
    
    # Save to CSV
    out_path = os.path.join("data", "emergency_dataset.csv")
    df.to_csv(out_path, index=False, encoding='utf-8')
    
    print(f"✅ Generated {len(df)} training samples")
    print(f"📁 Saved to: {out_path}")
    print("\n📊 Label distribution:")
    print(df["label"].value_counts())
    print("\n📝 Sample entries:")
    print(df.head(10))
    print("=" * 50)