import sys
print("Starting script...", flush=True)

import json
import joblib
import pandas as pd
print("Pandas imported...", flush=True)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
print("Sklearn imported...", flush=True)

import sys
import os
# Ensure we can import 'core' if running from root or elsewhere
# Scenario 1: Running from root (cwd=qxqbotv3) -> need to add ./al_rased
if os.path.exists("al_rased"):
    sys.path.append(os.path.abspath("al_rased"))
# Scenario 2: Running from al_rased (cwd=al_rased) -> need to add .
else:
    sys.path.append(os.getcwd())

from core.utils.text import normalize_text


# Define Base Dir based on script location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # .../al_rased
DATA_FILE = os.path.join(BASE_DIR, "data/labeledSamples/training_data.json")
MODEL_FILE = os.path.join(BASE_DIR, "features/model/classifier.joblib")
REPORT_FILE = os.path.join(BASE_DIR, "data/results/evaluation_report.txt")

# ============================================================
# FROZEN CATEGORIES — excluded from ML training
# These have too few samples and will be handled by keyword
# rules in engine.py. Unfreeze by adding more labeled samples
# and removing the category from this list.
# ============================================================
MIN_SAMPLES_THRESHOLD = 30  # Minimum samples needed for ML training

# Categories below threshold are auto-frozen, but you can also
# manually freeze categories here regardless of count:
MANUALLY_FROZEN = []

def get_frozen_categories(df):
    """Return list of categories to freeze (exclude from training)."""
    counts = df['label'].value_counts()
    auto_frozen = [label for label, count in counts.items()
                   if count < MIN_SAMPLES_THRESHOLD]
    return list(set(auto_frozen + MANUALLY_FROZEN))


def train_and_evaluate():
    print("Function called...", flush=True)
    # 1. Load Data
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file {DATA_FILE} not found.")
        return

    df = pd.DataFrame(raw_data)
    
    if df.empty:
        print("Error: Dataset is empty.")
        return

    print(f"Loaded {len(df)} samples.")
    
    # Apply Normalization
    print("Applying text normalization...", flush=True)
    df['text'] = df['text'].apply(normalize_text)
    
    print("Full class distribution:")
    print(df['label'].value_counts())

    # 1.5 Freeze weak categories
    frozen = get_frozen_categories(df)
    if frozen:
        frozen_counts = {cat: len(df[df['label'] == cat]) for cat in frozen}
        print(f"\n❄️  FROZEN CATEGORIES (excluded from training, <{MIN_SAMPLES_THRESHOLD} samples):")
        for cat, count in sorted(frozen_counts.items(), key=lambda x: x[1]):
            print(f"    ❄️  {cat}: {count} samples → handled by keyword rules")
        
        df_frozen = df[df['label'].isin(frozen)]
        df = df[~df['label'].isin(frozen)]
        print(f"\n📊 Training with {len(df)} samples ({len(df_frozen)} frozen)")
    else:
        print("\n✅ No categories frozen — all have sufficient samples")

    print("\nActive class distribution:")
    print(df['label'].value_counts())
    
    X = df['text']
    y = df['label']

    # 2. Pipeline Definition
    # TF-IDF -> Linear SVM (SGD) with log_loss for probabilities
    text_clf = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), analyzer='word')), 
        ('clf', SGDClassifier(loss='log_loss', penalty='l2', alpha=1e-3, random_state=42, max_iter=5, tol=None)),
    ])

    # 3. Cross-Validation Evaluation (since dataset is small)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    y_true_all = []
    y_pred_all = []
    
    print("\nRunning Cross-Validation...")
    for train_index, test_index in skf.split(X, y):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        
        text_clf.fit(X_train, y_train)
        predictions = text_clf.predict(X_test)
        
        y_true_all.extend(y_test)
        y_pred_all.extend(predictions)

    # 4. Final Training on Full Data
    text_clf.fit(X, y)
    joblib.dump(text_clf, MODEL_FILE)
    print(f"\nModel saved to {MODEL_FILE}")

    # 5. Reporting
    report = classification_report(y_true_all, y_pred_all, zero_division=0)
    conf_mat = confusion_matrix(y_true_all, y_pred_all, labels=text_clf.classes_)
    
    print("\nClassification Report (5-Fold CV):")
    print(report)
    
    print("\nConfusion Matrix:")
    print(text_clf.classes_)
    print(conf_mat)
    
    # Analyze logical gaps
    print("\n--- Logical Gap Analysis ---")
    
    # Convert confusion matrix to dataframe for easier reading
    cm_df = pd.DataFrame(conf_mat, index=text_clf.classes_, columns=text_clf.classes_)
    
    for cls in text_clf.classes_:
        # Check misclassified as Normal (False Negatives - Dangerous)
        # Check misclassified as Normal (False Negatives - Dangerous)
        if "طبيعي" in cm_df.columns:
            missed = cm_df.loc[cls, "طبيعي"]
            total = cm_df.loc[cls].sum()
            if cls != "طبيعي" and missed > 0:
                print(f"[RISK] {cls}: {missed}/{total} samples were misclassified as 'طبيعي'. Model missed these violations.")

    for cls in text_clf.classes_:
         # Check Normal misclassified as Violation (False Positives - Annoying)
        if cls == "طبيعي":
             for col in cm_df.columns:
                 if col != "طبيعي" and cm_df.loc["طبيعي", col] > 0:
                     print(f"[FALSE POSITIVE] طبيعي -> {col}: {cm_df.loc['طبيعي', col]} innocent messages flagged as {col}.")
                     
    # Identify classes with low support or low F1
    report_dict = classification_report(y_true_all, y_pred_all, output_dict=True, zero_division=0)
    for label, metrics in report_dict.items():
        if isinstance(metrics, dict) and 'f1-score' in metrics:
            if metrics['f1-score'] < 0.7:
                 print(f"[WEAKNESS] {label} has low F1-score ({metrics['f1-score']:.2f}). Needs more diverse samples.")

    # Save validation results
    import os
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w", encoding='utf-8') as f:
        f.write("Classification Report:\n")
        f.write(report)
        f.write("\n\nConfusion Matrix:\n")
        f.write(str(cm_df))

if __name__ == "__main__":
    train_and_evaluate()
