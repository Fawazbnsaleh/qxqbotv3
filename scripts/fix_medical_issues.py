
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔧 Fixing 'Medical Fraud' Category Issues...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    legit_fixed = 0
    multi_fixed = 0
    
    for sample in data:
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        if 'Medical Fraud' not in labels:
            continue
            
        text = sample['text']
        
        # 1. Fix Legitimate Questions (Move to Normal)
        # Context: "How do I upload sick leave?" -> Normal
        if 'كيف' in text or 'وين' in text or 'ارفع' in text:
            # Must NOT have commercial intent
            if not any(kw in text for kw in ['سعر', 'فلوس', 'تواصل', 'خاص', 'رقم', 'نسوي', 'نوفر']):
                # Double check: does it look like a student asking?
                if any(kw in text for kw in ['ارسل', 'ارفقه', 'دكتوره', 'جامعة', 'موقع']):
                    sample['labels'] = ['Normal']
                    sample['label'] = 'Normal'
                    sample['note'] = f"Auto-Fix: Medical Question -> Normal (Legitimate student inquiry)"
                    sample['reviewed_at'] = datetime.now().isoformat()
                    legit_fixed += 1
                    continue

        # 2. Add Academic Cheating label if missing
        academic_kws = ['اختبار', 'كويز', 'ميد', 'فاينل', 'درجات']
        if any(kw in text for kw in academic_kws):
            if 'Academic Cheating' not in labels and 'Normal' not in sample.get('labels', []):
                 labels.append('Academic Cheating')
                 sample['labels'] = labels
                 sample['note'] += " + Added Academic Cheating (Context)"
                 multi_fixed += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Reverted {legit_fixed} legitimate questions to 'Normal'.")
    print(f"✅ Added 'Academic Cheating' to {multi_fixed} samples.")

if __name__ == "__main__":
    main()
