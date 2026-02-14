
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🚑 Applying Emergency Cross-Category Fixes...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    fixed_count = 0
    
    for sample in data:
        labels = sample.get('labels', [sample.get('label')])
        text = sample['text'].lower()
        original_label = labels[0]
        new_label = None
        
        # 1. Fix Unethical -> Academic Cheating
        if 'Unethical' in labels:
            if any(kw in text for kw in ['خدمات طلابية', 'بحوث', 'رسائل', 'ماجستير', 'منصة', 'واجب']):
                new_label = 'Academic Cheating'
        
        # 2. Fix Hacking -> Financial Scams
        elif 'Hacking' in labels:
            if any(kw in text for kw in ['ربح', 'استثمار', 'كريبتو', 'crypto', 'تداول', 'اموال', 'دولار']):
                new_label = 'Financial Scams'

        # Apply Fix
        if new_label:
            sample['labels'] = [new_label]
            sample['label'] = new_label
            sample['note'] = f"Cross-Category Fix: {text[:20]}... [{original_label} -> {new_label}]"
            sample['reviewed_at'] = datetime.now().isoformat()
            fixed_count += 1
            # print(f"Fixed: {original_label} -> {new_label}")

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Fixed {fixed_count} cross-category errors.")

if __name__ == "__main__":
    main()
