
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🧹 Cleaning 'Unethical' Category Pollution...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    clean_count = 0
    
    for sample in data:
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        if 'Unethical' not in labels:
            continue
            
        text = sample['text']
        new_label = None
        
        # Crypto News / Trading -> Financial Scams (or Normal if just news, but let's be safe with Financial/Spam)
        if any(kw in text.lower() for kw in ['binance', 'بينانس', 'bitcoin', 'بتكوين', 'تداول', 'إدراج', 'pairs', 'usdt']):
            # If it sounds like a scam (pump/dump/profit), Financial. If just news, maybe Spam?
            if any(kw in text for kw in ['كسبانين', 'ربح', 'سجل', 'مجان', 'توصيات']):
                new_label = 'Financial Scams'
            else:
                new_label = 'Spam' # Treat crypto news spam as Spam
        
        if new_label:
            sample['labels'] = [new_label]
            sample['label'] = new_label
            sample['note'] = f"Auto-Fix: Unethical -> {new_label} (Crypto pollution removed)"
            sample['reviewed_at'] = datetime.now().isoformat()
            clean_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Removed {clean_count} polluted samples from 'Unethical'.")

if __name__ == "__main__":
    main()
