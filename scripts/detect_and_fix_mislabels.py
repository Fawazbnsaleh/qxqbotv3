
import json
import joblib
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_predict, StratifiedKFold

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🧠 Detecting Mislabels using Cross-Validation (True Validation Errors)...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    df['primary_label'] = df['labels'].apply(lambda x: x[0] if isinstance(x, list) and x else (x if isinstance(x, str) else 'Normal'))
    
    text_clf = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=2)), 
        ('clf', SGDClassifier(loss='log_loss', penalty='l2', alpha=1e-4, random_state=42, max_iter=20)),
    ])
    
    X = df['text']
    y = df['primary_label']
    
    print("Running 5-Fold CV to get unbiased predictions...")
    # Get probability estimates (needs method='predict_proba' which isn't standard in cross_val_predict for all models, 
    # but SGDClassifier with log_loss supports it. However cross_val_predict with method='predict_proba' works).
    
    y_pred_probs = cross_val_predict(text_clf, X, y, cv=5, method='predict_proba', n_jobs=-1)
    
    # We need to map probs back to classes. 
    # To do this safely, we need to know the class order. 
    # We'll fit the model once on 1 sample to get classes_, or just fit on full data to get mapping (assuming classes don't change).
    text_clf.fit(X, y) 
    classes = text_clf.classes_
    
    fix_count = 0
    fixed_samples = []

    for i in range(len(df)):
        original_label = df.loc[i, 'primary_label']
        
        # We are only interested in Normal samples that are predicted as something else
        if original_label != 'Normal':
            continue
            
        # Get prediction from CV
        probs = y_pred_probs[i]
        top_class_idx = np.argmax(probs)
        pred_label = classes[top_class_idx]
        confidence = probs[top_class_idx]
        
        if pred_label == 'Normal':
            continue
            
        print(f"[{i}] Normal -> {pred_label} ({confidence:.2f}) | {df.loc[i, 'text'][:40]}...")

        # Apply Fix if confidence is moderate (>0.40) but supported by keywords
        if confidence > 0.40:
             text = df.loc[i, 'text']
             
             should_fix = False
             if pred_label == 'Academic Cheating':
                 if any(kw in text for kw in ['حل', 'واجب', 'بحث', 'تخرج', 'مشروع', 'مساعدة', 'تكاليف', 'دكتور', 'استفسار', 'جامعة', 'طلاب', 'اسايمنت', 'كويز', 'اختبار']):
                      should_fix = True
             elif pred_label == 'Financial Scams':
                 if any(kw in text for kw in ['ربح', 'استثمار', 'ريال', 'دولار', 'محفظة', 'تداول', 'كريبتو', 'عملات', 'سهم', 'توصيات']):
                      should_fix = True
             elif pred_label == 'Medical Fraud':
                 if any(kw in text for kw in ['سكليف', 'طبي', 'اجازة', 'مرضية', 'منصة صحتي', 'عذر']):
                      should_fix = True
             elif pred_label == 'Spam':
                 if any(kw in text for kw in ['حياكم', 'رابط', 'متجر', 'قروب', 'دعم', 'سيرفر', 'افتتاح', 'عرض']):
                      should_fix = True
             
             if should_fix:
                 data[i]['labels'] = [pred_label]
                 data[i]['label'] = pred_label
                 data[i]['note'] = f"Auto-Fix: CV Prediction {pred_label} ({confidence:.2f})"
                 data[i]['reviewed_at'] = datetime.now().isoformat()
                 fixed_samples.append({'text': text[:40], 'new': pred_label})
                 fix_count += 1

    if fix_count > 0:
        with open(data_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    print(f"\n✅ Auto-Corrected {fix_count} samples based on CV Predictions.")
    for s in fixed_samples[:10]:
        print(f"   -> {s['new']}: {s['text']}...")

if __name__ == "__main__":
    main()
