
import json
import joblib
import os
import sys
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔬 Analyzing False Positives (Normal labeled as Violation)...")
    
    # Reload data
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    # Handle label/labels
    df['primary_label'] = df['labels'].apply(lambda x: x[0] if isinstance(x, list) and x else (x if isinstance(x, str) else 'Normal'))
    
    # Load Model (assuming it was just saved by train.py)
    # Actually, let's just retrain in-memory to be sure we match the logic
    print("   Retraining in-memory to reproduce errors...")
    
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, min_df=2)
    X = vectorizer.fit_transform(df['text'])
    y = df['primary_label']
    
    model = LogisticRegression(class_weight='balanced', max_iter=1000, C=1.0)
    model.fit(X, y)
    
    preds = model.predict(X)
    
    df['pred'] = preds
    
    # 1. Analyze Normal -> Academic Cheating (72 samples)
    fp_academic = df[(df['primary_label'] == 'Normal') & (df['pred'] == 'Academic Cheating')]
    print(f"\n🚨 Normal -> Academic Cheating ({len(fp_academic)} samples):")
    for txt in fp_academic['text'].head(20):
        print(f"   - {txt[:80]}...")
        
    # Check top features for Academic Cheating
    feature_names = vectorizer.get_feature_names_out()
    coefs = model.coef_[model.classes_ == 'Academic Cheating'][0]
    top_indices = coefs.argsort()[-20:][::-1]
    print("\n🔑 Top Keywords driving 'Academic Cheating':")
    print([feature_names[i] for i in top_indices])

if __name__ == "__main__":
    main()
