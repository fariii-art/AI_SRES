"""
ai/model.py — Emergency classification model (TF-IDF based)
No transformers required - works with any Python environment
"""

import re
import os
import pickle
import logging
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

logger = logging.getLogger(__name__)

MODEL_CACHE_PATH = "sers_model.pkl"

# Emergency categories
CATEGORIES = ["Fire", "Accident", "Medical", "Crime", "Flood", "Earthquake"]

# Sample training data (built-in, no external files needed)
SAMPLE_DATA = [
    # Fire
    ("fire in building downtown", "Fire"),
    ("house on fire need help", "Fire"),
    ("آگ لگ گئی عمارت میں", "Fire"),
    ("wildfire spreading near residential area", "Fire"),
    ("kitchen fire gas cylinder explosion", "Fire"),
    ("chemical factory fire toxic smoke", "Fire"),
    ("vehicle on fire on highway", "Fire"),
    ("smoke detected in apartment building", "Fire"),
    
    # Accident
    ("car crash on highway multiple vehicles", "Accident"),
    ("road accident at intersection injuries", "Accident"),
    ("truck overturned blocking traffic", "Accident"),
    ("motorcycle accident rider unconscious", "Accident"),
    ("pedestrian hit by speeding car", "Accident"),
    ("bus collided with car passengers injured", "Accident"),
    ("کار حادثہ ہو گیا", "Accident"),
    
    # Medical
    ("heart attack patient needs ambulance", "Medical"),
    ("unconscious person found on street", "Medical"),
    ("severe bleeding from accident wound", "Medical"),
    ("difficulty breathing asthma attack", "Medical"),
    ("stroke symptoms elderly patient", "Medical"),
    ("pregnant woman in labor emergency", "Medical"),
    ("child having seizure at school", "Medical"),
    ("دل کا دورہ پڑ رہا ہے", "Medical"),
    
    # Crime
    ("robbery in progress at bank", "Crime"),
    ("armed assault reported with weapon", "Crime"),
    ("shooting heard in neighborhood", "Crime"),
    ("house break-in family trapped", "Crime"),
    ("carjacking at gunpoint", "Crime"),
    ("domestic violence incident", "Crime"),
    ("kidnapping reported child taken", "Crime"),
    ("ڈکیتی ہو رہی ہے", "Crime"),
    
    # Flood
    ("flash flood in residential area", "Flood"),
    ("river overflowing homes submerged", "Flood"),
    ("people trapped on roof rising water", "Flood"),
    ("urban flooding streets underwater", "Flood"),
    ("dam overflow warning evacuate", "Flood"),
    ("landslide blocking road to village", "Flood"),
    ("سیلاب آ گیا ہے", "Flood"),
    
    # Earthquake
    ("earthquake tremors felt strongly", "Earthquake"),
    ("buildings shaking ground moving", "Earthquake"),
    ("aftershocks continuing after quake", "Earthquake"),
    ("structural damage from earthquake", "Earthquake"),
    ("people evacuating buildings", "Earthquake"),
    ("زلزلہ محسوس ہوا", "Earthquake"),
]


class EmergencyModel:
    """
    Emergency incident classifier using TF-IDF + Logistic Regression
    Lightweight and works without external dependencies
    """
    
    def __init__(self, force_retrain: bool = False):
        self.pipeline = None
        self.classes_ = None
        self.eval_accuracy = None
        self.eval_report = None
        
        if not force_retrain and Path(MODEL_CACHE_PATH).exists():
            self._load()
        else:
            self._train()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        text = text.lower()
        # Keep letters, numbers, spaces, and Urdu characters
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    
    def _generate_more_data(self):
        """Generate additional synthetic training data"""
        import random
        
        templates = {
            "Fire": [
                "fire at {location}", "blaze in {location}", "burning building {location}",
                "smoke coming from {location}", "flames visible at {location}"
            ],
            "Accident": [
                "crash on {location}", "accident at {location}", "collision on {location}",
                "vehicle overturned {location}", "pileup on {location}"
            ],
            "Medical": [
                "medical emergency at {location}", "person injured at {location}",
                "heart attack at {location}", "bleeding at {location}"
            ],
            "Crime": [
                "crime scene at {location}", "robbery at {location}", "assault at {location}",
                "police needed at {location}"
            ],
            "Flood": [
                "flooding at {location}", "water rising at {location}", "rescue needed at {location}"
            ],
            "Earthquake": [
                "earthquake at {location}", "tremors at {location}", "shaking at {location}"
            ]
        }
        
        locations = ["main street", "downtown", "hospital road", "school", "market", "highway", "residential area"]
        languages = ["", " urgent", " help", " immediately", " please"]
        
        samples = []
        for _ in range(500):
            for category, tmpl_list in templates.items():
                text = random.choice(tmpl_list).format(location=random.choice(locations))
                text += random.choice(languages)
                samples.append((text, category))
        
        return samples
    
    def _train(self):
        """Train the model"""
        logger.info("Training emergency classification model...")
        
        # Combine built-in data with generated data
        all_data = SAMPLE_DATA.copy()
        all_data.extend(self._generate_more_data())
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data, columns=['text', 'label'])
        df['clean_text'] = df['text'].apply(self._clean_text)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            df['clean_text'], df['label'],
            test_size=0.2,
            random_state=42,
            stratify=df['label']
        )
        
        # Create pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                analyzer='char_wb',
                ngram_range=(2, 4),
                max_features=10000,
                sublinear_tf=True
            )),
            ('clf', LogisticRegression(
                C=1.0,
                class_weight='balanced',
                max_iter=1000,
                solver='lbfgs'
            ))
        ])
        
        # Train
        self.pipeline.fit(X_train, y_train)
        self.classes_ = self.pipeline.classes_
        
        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        self.eval_accuracy = round(accuracy_score(y_test, y_pred) * 100, 1)
        self.eval_report = classification_report(y_test, y_pred)
        
        logger.info(f"Model trained. Accuracy: {self.eval_accuracy}%")
        
        # Save
        self._save()
    
    def _save(self):
        """Save model to disk"""
        with open(MODEL_CACHE_PATH, 'wb') as f:
            pickle.dump({
                'pipeline': self.pipeline,
                'classes_': self.classes_,
                'eval_accuracy': self.eval_accuracy,
                'eval_report': self.eval_report
            }, f)
        logger.info(f"Model saved to {MODEL_CACHE_PATH}")
    
    def _load(self):
        """Load model from disk"""
        with open(MODEL_CACHE_PATH, 'rb') as f:
            data = pickle.load(f)
        self.pipeline = data['pipeline']
        self.classes_ = data['classes_']
        self.eval_accuracy = data['eval_accuracy']
        self.eval_report = data['eval_report']
        logger.info(f"Model loaded. Accuracy: {self.eval_accuracy}%")
    
    def predict(self, text: str):
        """
        Predict emergency category
        
        Returns:
            category: str
            confidence: float
            prob_dict: dict
        """
        if not text or len(text.strip()) < 3:
            return "Unknown", 0.0, {}
        
        clean = self._clean_text(text)
        
        if hasattr(self.pipeline, 'predict_proba'):
            probs = self.pipeline.predict_proba([clean])[0]
            pred_idx = probs.argmax()
            confidence = float(probs[pred_idx])
            category = self.classes_[pred_idx]
            
            prob_dict = {cls: float(p) for cls, p in zip(self.classes_, probs)}
        else:
            category = self.pipeline.predict([clean])[0]
            confidence = 0.8
            prob_dict = {}
        
        return category, confidence, prob_dict


# For backward compatibility
EmergencyAIModel = EmergencyModel
MultilingualEmergencyModel = EmergencyModel
