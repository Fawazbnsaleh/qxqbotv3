
import json
import os
import sys
import joblib

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from al_rased.features.detection.engine import DetectionEngine
from al_rased.core.utils.text import normalize_text

def main():
    print("🕵️ Analyzing False Negatives (ML Misses)...")
    
    # Load Model & Data
    DetectionEngine.load_model()
    model = DetectionEngine._model
    # vectorizer is part of the pipeline usually
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    print(f"Loaded {len(data)} samples.")
    
    misses = []
    
    for i, sample in enumerate(data):
        text = sample['text']
        true_label = sample.get('labels', [sample.get('label')])[0]
        
        # 1. ML Prediction ONLY (Bypass Hybrid to see ML weakness)
        # Model pipeline handles normalization and vectorization if trained that way
        processed_text = normalize_text(text)
        
        try:
            pred_label = model.predict([processed_text])[0]
            prob = max(model.predict_proba([processed_text])[0])
        except:
            continue
        
        if pred_label != true_label:
            # Check if Hybrid would fix it?
            hybrid_res = DetectionEngine.predict(text)
            caught_by_hybrid = (hybrid_res['label'] == true_label)
            
            misses.append({
                'text': text[:60],
                'true': true_label,
                'pred': pred_label,
                'conf': prob,
                'hybrid_fix': caught_by_hybrid
            })

    print(f"\n📉 Total ML Misses: {len(misses)} / {len(data)} ({len(misses)/len(data):.1%})")
    
    # Group by category
    from collections import Counter
    cat_misses = Counter([m['true'] for m in misses])
    
    print("\n📊 Misses by Category:")
    for cat, count in cat_misses.most_common():
        print(f"{cat}: {count}")

    print("\n🛡️ Hybrid Safety Net Check:")
    fixed_by_hybrid = len([m for m in misses if m['hybrid_fix']])
    print(f"Examples ONLY missed by ML but CAUGHT by Keywords: {fixed_by_hybrid}")
    
    print("\n⚠️ Truly Missed (Both ML & Keywords failed):")
    truly_missed = [m for m in misses if not m['hybrid_fix']]
    print(f"Count: {len(truly_missed)}")
    
    if truly_missed:
        print("\nTop 10 Truly Missed Examples:")
        for m in truly_missed[:10]:
            print(f"- [{m['true']} -> {m['pred']}] {m['text']}...")

if __name__ == "__main__":
    main()
