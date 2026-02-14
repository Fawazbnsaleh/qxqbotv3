
import json
import pandas as pd
import numpy as np
import os
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_predict

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔬 Deep Analysis of False Positives (Normal -> Violation)...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    df['primary_label'] = df['labels'].apply(lambda x: x[0] if isinstance(x, list) and x else (x if isinstance(x, str) else 'Normal'))
    
    # Setup Pipeline matching train.py
    text_clf = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=2)), 
        ('clf', SGDClassifier(loss='log_loss', penalty='l2', alpha=1e-3, random_state=42, max_iter=5)),
    ])
    
    X = df['text']
    y = df['primary_label']
    
    print("Running Cross-Validation to identify the 80 False Positives...")
    y_pred = cross_val_predict(text_clf, X, y, cv=5)
    
    df['pred'] = y_pred
    
    # Filter: True Label = Normal, Predicted = Academic Cheating (or others)
    fp_academic = df[(df['primary_label'] == 'Normal') & (df['pred'] == 'Academic Cheating')]
    fp_financial = df[(df['primary_label'] == 'Normal') & (df['pred'] == 'Financial Scams')]
    fp_medical = df[(df['primary_label'] == 'Normal') & (df['pred'] == 'Medical Fraud')]
    fp_spam = df[(df['primary_label'] == 'Normal') & (df['pred'] == 'Spam')]
    
    print(f"\n🚨 Normal -> Academic Cheating ({len(fp_academic)} samples):")
    for txt in fp_academic['text'].head(30):
        print(f"   - {txt[:80]}...")

    print(f"\n💰 Normal -> Financial Scams ({len(fp_financial)} samples):")
    for txt in fp_financial['text'].head(10):
        print(f"   - {txt[:80]}...")

    print(f"\n⚕️ Normal -> Medical Fraud ({len(fp_medical)} samples):")
    for txt in fp_medical['text'].head(10):
        print(f"   - {txt[:80]}...")
        
    print(f"\n📢 Normal -> Spam ({len(fp_spam)} samples):")
    for txt in fp_spam['text'].head(10):
        print(f"   - {txt[:80]}...")

if __name__ == "__main__":
    main()
