
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔧 Fixing Remaining Categories...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    fixed_count = 0
    
    for sample in data:
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        text = sample['text']
        original_label = labels[0]
        new_label = None

        # 1. Hacking -> Spam (Game Servers)
        if 'Hacking' in labels:
            if any(kw in text for kw in ['ماين كرافت', 'سيرفر', 'craft', 'افتتاح']):
                # Only if it DOESN'T mention "DDOS" or "Attack" or "Hack"
                if not any(kw in text.lower() for kw in ['ddos', 'hack', 'اختراق']):
                    new_label = 'Spam'

        # 2. Unethical -> Academic
        if 'Unethical' in labels:
            if 'تحويل أفكارك إلى واقع رقمي' in text:
                 new_label = 'Academic Cheating'

        # 3. Spam -> Hacking (Ethical Hacker Ad)
        if 'Spam' in labels:
            if 'مهكر اخلاقي' in text:
                new_label = 'Hacking'

        # Apply Fix
        if new_label:
            sample['labels'] = [new_label]
            sample['label'] = new_label
            sample['note'] = f"Auto-Fix: {original_label} -> {new_label} (Audit found context error)"
            sample['reviewed_at'] = datetime.now().isoformat()
            fixed_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Fixed {fixed_count} remaining category issues.")

if __name__ == "__main__":
    main()
