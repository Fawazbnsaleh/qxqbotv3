
import json
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from al_rased.features.detection.engine import DetectionEngine

def main():
    print("🤖 Testing Hybrid Engine (ML + Expert Rules)...")
    
    # Load Engine
    DetectionEngine.load_model()
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Focus on weak categories
    weak_cats = ['Unethical', 'Hacking', 'Spam']
    
    results = {cat: {'total': 0, 'detected': 0, 'missed': 0} for cat in weak_cats}
    
    missed_samples = []

    for sample in data:
        # Get primary label
        labels = sample.get('labels', [sample.get('label')])
        if not labels or labels[0] not in weak_cats:
            continue
            
        true_label = labels[0]
        text = sample['text']
        
        # Hybrid Prediction
        pred = DetectionEngine.predict(text)
        pred_label = pred['label']
        
        results[true_label]['total'] += 1
        
        # Check if match
        if pred_label == true_label:
             results[true_label]['detected'] += 1
        else:
             results[true_label]['missed'] += 1
             if len(missed_samples) < 10:
                 missed_samples.append({
                     'text': text[:50],
                     'true': true_label,
                     'pred': pred_label,
                     'reason': pred.get('matched_keyword', 'ML Prediction')
                 })

    # Print Report
    print("\n📊 Hybrid Engine Performance:")
    print(f"| Category | Total | Detected | Missed | Accuracy |")
    print("|---|---|---|---|---|")
    for cat, stat in results.items():
        if stat['total'] > 0:
            acc = stat['detected'] / stat['total']
            print(f"| {cat:<10} | {stat['total']:<5} | {stat['detected']:<5} | {stat['missed']:<5} | {acc:.1%} |")
    
    if missed_samples:
        print("\n📝 Sample Misses:")
        for s in missed_samples:
            print(f"- [{s['true']} -> {s['pred']}] Text: {s['text']}... (Source: {s['reason']})")

if __name__ == "__main__":
    main()
