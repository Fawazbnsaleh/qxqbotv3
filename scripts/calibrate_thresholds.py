"""
Auto-Calibration Script for Detection Thresholds.
Analyzes training data to find optimal threshold per category.
"""
import sys
import os
import json
import joblib
import numpy as np

sys.path.append(os.path.join(os.getcwd(), 'al_rased'))
from core.utils.text import normalize_text

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"
MODEL_FILE = "al_rased/features/model/classifier.joblib"
OUTPUT_FILE = "al_rased/features/detection/thresholds.json"

def calibrate():
    # 1. Load Model and Data
    print("Loading model and training data...")
    clf = joblib.load(MODEL_FILE)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 2. Predict on Training Data (to find confidence distribution)
    texts = [normalize_text(d['text']) for d in data]
    labels = [d['label'] for d in data]
    
    probas = clf.predict_proba(texts)
    preds = clf.predict(texts)
    classes = list(clf.classes_)
    
    # 3. Calculate Thresholds
    # For each category, find the minimum confidence that correctly predicts it
    # We want threshold = (mean of correct predictions) - 1 * std
    # This ensures we catch most true positives while staying above noise
    
    thresholds = {}
    
    for cat in classes:
        if cat == "Normal":
            continue
            
        cat_idx = classes.index(cat)
        
        # Get confidence for TRUE POSITIVES (correctly predicted as this category)
        true_positive_confs = []
        for i, true_label in enumerate(labels):
            if true_label == cat and preds[i] == cat:
                true_positive_confs.append(probas[i][cat_idx])
        
        if true_positive_confs:
            mean_conf = np.mean(true_positive_confs)
            std_conf = np.std(true_positive_confs)
            # Set threshold at mean - 1.5*std (aggressive) but minimum 0.30
            suggested_threshold = max(0.30, mean_conf - 1.5 * std_conf)
            thresholds[cat] = round(suggested_threshold, 2)
            print(f"{cat}: Mean Conf = {mean_conf:.2f}, Std = {std_conf:.2f} -> Threshold = {thresholds[cat]}")
        else:
            # No true positives? Use conservative default
            thresholds[cat] = 0.50
            print(f"{cat}: No true positives found, using default 0.50")
    
    # 4. Save Thresholds
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(thresholds, f, indent=2, ensure_ascii=False)
    
    print(f"\nThresholds saved to {OUTPUT_FILE}")
    print("Final Thresholds:", thresholds)
    
    return thresholds

if __name__ == "__main__":
    calibrate()
