"""
build_dataset.py – Assemble a 5 000-sample bilingual emergency dataset.

Fixed issues:
- Bare except replaced with specific Exception catches + print messages.
- emotion_map applied with .map() but unmapped rows now filled with 'General'
  instead of being silently dropped (preserving sample count).
- TARGET_SIZE sampling uses replace=False only when df is large enough,
  otherwise pads with synthetic data.
- All file paths use os.path so they work cross-platform.
"""

import os
import random
import pandas as pd
from sklearn.utils import shuffle

os.makedirs("data", exist_ok=True)

TARGET_SIZE = 5_000
CATEGORIES  = ["Fire", "Accident", "Medical", "Crime", "Flood", "Earthquake"]


# ---------------------------------------------------------------------------
# Source 1: Optional Kaggle emotion dataset
# ---------------------------------------------------------------------------

def load_emotion_dataset() -> pd.DataFrame | None:
    """
    Attempt to load the Kaggle Roman-Urdu emotion Excel.
    Returns a DataFrame or None if unavailable.
    """
    path = "RU-EN-Emotion_Dataset.xlsx"
    if not os.path.exists(path):
        print("⚠️  Emotion dataset not found – skipping.")
        return None
    try:
        df = pd.read_excel(path)
        emotion_map = {
            "Fear":     "General",
            "Anger":    "Crime",
            "Sad":      "Medical",
            "Happy":    "General",
            "Surprise": "Accident",
        }
        if "emotion" in df.columns and "text" in df.columns:
            df["label"] = df["emotion"].map(emotion_map).fillna("General")
            df = df[["text", "label"]].dropna(subset=["text"])
            print(f"✅ Loaded {len(df)} records from emotion dataset.")
            return df
        print("⚠️  Emotion dataset missing expected columns – skipping.")
        return None
    except Exception as exc:
        print(f"⚠️  Could not read emotion dataset ({exc}) – skipping.")
        return None


# ---------------------------------------------------------------------------
# Source 2: Urdu news sample (built-in)
# ---------------------------------------------------------------------------

def load_news_sample() -> pd.DataFrame:
    news_data = [
        ("آگ لگنے سے تین افراد جاں بحق",         "Fire"),
        ("کار حادثہ میں پانچ زخمی",               "Accident"),
        ("دل کا دورہ پڑنے سے مریض کی موت",        "Medical"),
        ("ڈکیتی کے دوران مزاحمت پر فائرنگ",       "Crime"),
        ("سیلاب سے ہزاروں گھر زیر آب",            "Flood"),
        ("شدید زلزلے کے جھٹکے محسوس کئے گئے",    "Earthquake"),
    ]
    expanded = [
        {"text": f"{text} {i}", "label": label}
        for i in range(200)
        for text, label in news_data
    ]
    df = pd.DataFrame(expanded)
    print(f"✅ Added {len(df)} Urdu news samples.")
    return df


# ---------------------------------------------------------------------------
# Source 3: English emergency phrases
# ---------------------------------------------------------------------------

def load_emergency_phrases() -> pd.DataFrame:
    phrases: dict[str, list[str]] = {
        "Fire":       ["fire in building", "house on fire", "wildfire spreading", "smoke detected"],
        "Accident":   ["car crash", "road accident", "vehicle collision", "truck overturned"],
        "Medical":    ["heart attack", "unconscious person", "bleeding severe", "difficulty breathing"],
        "Crime":      ["robbery in progress", "armed assault", "shooting heard", "theft reported"],
        "Flood":      ["flood warning", "water rising", "river overflowing", "homes submerged"],
        "Earthquake": ["earthquake felt", "ground shaking", "tremor strong", "buildings swaying"],
    }
    rows = [{"text": text, "label": cat} for cat, texts in phrases.items() for text in texts]
    df = pd.DataFrame(rows)
    df = pd.concat([df] * 10, ignore_index=True)   # ~40 → 400 per category
    print(f"✅ Added {len(df)} English emergency phrases.")
    return df


# ---------------------------------------------------------------------------
# Synthetic fallback
# ---------------------------------------------------------------------------

_TEXTS_EN = [
    "Emergency: Fire reported", "Car accident on highway",
    "Patient needs medical help", "Robbery at gunpoint",
    "Flood water entering homes", "Earthquake tremors felt",
    "Building on fire", "Multiple vehicle crash",
    "Heart attack symptoms", "Theft in progress",
    "Rising flood levels", "Strong earthquake aftershocks",
]
_TEXTS_UR = [
    "آگ لگ گئی", "کار حادثہ پیش آیا",
    "مریض کو فوری طبی امداد چاہیے", "ڈکیتی ہو رہی ہے",
    "سیلاب کا پانی گھروں میں داخل", "زلزلے کے جھٹکے محسوس ہوئے",
    "عمارت میں آگ لگی", "گاڑیوں کی ٹکر",
    "دل کا دورہ پڑ رہا ہے", "چوری ہو رہی ہے",
    "سیلاب کی سطح بڑھ رہی", "زلزلے کے جھٹکے",
]


def generate_synthetic_data(n: int) -> pd.DataFrame:
    pool = _TEXTS_EN + _TEXTS_UR
    rows = [
        {"text": random.choice(pool), "label": random.choice(CATEGORIES)}
        for _ in range(n)
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_dataset() -> pd.DataFrame:
    print("🚀 Building bilingual dataset…")

    frames: list[pd.DataFrame] = []

    emotion_df = load_emotion_dataset()
    if emotion_df is not None:
        frames.append(emotion_df)

    frames.append(load_news_sample())
    frames.append(load_emergency_phrases())

    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # Pad or trim to TARGET_SIZE
    if len(df) < TARGET_SIZE:
        needed   = TARGET_SIZE - len(df)
        df_synth = generate_synthetic_data(needed)
        df       = pd.concat([df, df_synth], ignore_index=True)
        print(f"✅ Added {needed} synthetic samples to reach {TARGET_SIZE}.")
    else:
        df = df.sample(n=TARGET_SIZE, random_state=42, replace=False)

    df = shuffle(df, random_state=42).reset_index(drop=True)
    out_path = os.path.join("data", "emergency_dataset.csv")
    df.to_csv(out_path, index=False)

    print(f"✅ Dataset saved: {len(df)} records → {out_path}")
    print("Label distribution:")
    print(df["label"].value_counts())
    return df


if __name__ == "__main__":
    build_dataset()