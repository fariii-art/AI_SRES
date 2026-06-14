"""
train_model.py – Fine-tune XLM-RoBERTa on the SERS emergency dataset.

Fixed issues:
- evaluation_strategy renamed to eval_strategy (required by transformers ≥ 4.41).
- tokenizer= kwarg removed from Trainer (deprecated in recent transformers; causes
  a warning/error and is no longer needed for training).
- load_data() column-detection logic fixed: only renames columns that are NOT
  already named 'text'/'label', preventing a KeyError when both are present.
- confusion_matrix called with labels= list of ints to prevent index mismatch when
  validation set doesn't contain all classes.
- Explicit os.makedirs for 'results' and 'logs' so training never fails on a clean
  checkout.
- MODEL_SIGNATURE written as the last step so a partial run doesn't leave a valid
  signature on a broken model.
"""

import os
import json
import logging

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from datasets import Dataset
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs("models/emergency_model", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("logs",    exist_ok=True)

ALLOWED_LABELS = ["Fire", "Accident", "Medical", "Crime", "Flood", "Earthquake"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(csv_path: str = "data/emergency_dataset.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Normalise column names only if they are missing
    if "text" not in df.columns:
        for col in df.columns:
            if df[col].dtype == object and col != "label":
                df = df.rename(columns={col: "text"})
                break
    if "label" not in df.columns:
        for col in df.columns:
            if df[col].dtype == object and col != "text":
                df = df.rename(columns={col: "label"})
                break

    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("CSV must have 'text' and 'label' columns.")

    # Map unknown categories to 'General' (keep only allowed labels)
    all_labels = ALLOWED_LABELS + ["General"]
    df["label"] = df["label"].apply(lambda x: x if x in all_labels else "General")
    return df


df = load_data()
labels_list = sorted(df["label"].unique())
label2id    = {l: i for i, l in enumerate(labels_list)}
id2label    = {i: l for l, i in label2id.items()}
df["label_id"] = df["label"].map(label2id)

# ---------------------------------------------------------------------------
# Train / validation split
# ---------------------------------------------------------------------------

train_texts, val_texts, train_labels, val_labels = train_test_split(
    df["text"].tolist(),
    df["label_id"].tolist(),
    test_size=0.2,
    random_state=42,
    stratify=df["label_id"].tolist(),   # balanced split
)

# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

MODEL_NAME = "xlm-roberta-base"
tokenizer  = AutoTokenizer.from_pretrained(MODEL_NAME)


def tokenize_function(examples: dict) -> dict:
    return tokenizer(
        examples["text"],
        padding="max_length",
        truncation=True,
        max_length=128,
    )


train_dataset = Dataset.from_dict({"text": train_texts, "label": train_labels})
val_dataset   = Dataset.from_dict({"text": val_texts,   "label": val_labels})
train_dataset = train_dataset.map(tokenize_function, batched=True)
val_dataset   = val_dataset.map(tokenize_function,   batched=True)

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(labels_list),
    id2label=id2label,
    label2id=label2id,
    ignore_mismatched_sizes=True,
)

# ---------------------------------------------------------------------------
# Training arguments
# ---------------------------------------------------------------------------

training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="epoch",          # correct kwarg name (transformers ≥ 4.41)
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    logging_dir="./logs",
)


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return {"accuracy": accuracy_score(labels, predictions)}


trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    # tokenizer kwarg intentionally omitted (deprecated in transformers ≥ 4.46)
)

# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------

trainer.train()

# ---------------------------------------------------------------------------
# Save model & tokeniser
# ---------------------------------------------------------------------------

model.save_pretrained("models/emergency_model")
tokenizer.save_pretrained("models/emergency_model")
logger.info("Model saved to models/emergency_model/")

# ---------------------------------------------------------------------------
# Confusion matrix
# ---------------------------------------------------------------------------

preds_output = trainer.predict(val_dataset)
y_true = val_labels
y_pred = np.argmax(preds_output.predictions, axis=1).tolist()

cm = confusion_matrix(y_true, y_pred, labels=list(range(len(labels_list))))

with open("models/emergency_model/confusion_matrix.json", "w") as f:
    json.dump({"matrix": cm.tolist(), "labels": labels_list}, f)

logger.info("Confusion matrix saved.")

# ---------------------------------------------------------------------------
# Model signature  (written last so partial runs don't leave a valid sig)
# ---------------------------------------------------------------------------

signature = os.getenv("MODEL_SIGNATURE", "sers_v1_2025")
with open("models/emergency_model/signature.txt", "w") as f:
    f.write(signature)

val_acc = accuracy_score(y_true, y_pred)
print(f"\n✅ Training complete.")
print(f"   Validation accuracy : {val_acc:.3f}")
print(f"   Labels              : {labels_list}")
print(f"   Saved to            : models/emergency_model/")
