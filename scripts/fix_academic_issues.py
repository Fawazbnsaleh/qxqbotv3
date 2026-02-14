
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔧 Fixing Academic Cheating Category...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    med_fix_count = 0
    legit_fix_count = 0
    
    for sample in data:
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        if 'Academic Cheating' not in labels:
            continue
            
        text = sample['text']
        
        # 1. Fix Medical Fraud Leaks
        # If it has specific medical fraud keywords, ADD Medical Fraud label
        med_kws = ['سكليف', 'اعذار طبية', 'عذر طبي', 'صحتي', 'مرضية', 'اجازة مرضية']
        if any(kw in text for kw in med_kws):
            if 'Medical Fraud' not in labels:
                labels.append('Medical Fraud')
                sample['labels'] = labels
                # If mostly medical (e.g. starts with medical terms), set primary label to Medical Fraud
                if re.match(r'.*(' + '|'.join(med_kws) + ')', text[:30]):
                    sample['label'] = 'Medical Fraud'
                sample['note'] = f"Auto-Fix: Added Medical Fraud label (Found keywords) [Originally Academic]"
                sample['reviewed_at'] = datetime.now().isoformat()
                med_fix_count += 1

        # 2. Fix Legitimate Groups (False Positives)
        # If it's just a group link without explicit cheating offer
        if 'قروب' in text and not any(kw in text for kw in ['حل واجب', 'حل اختبار', 'بفلوس', 'سعر', 'الدفع']):
             # Check if it's likely a general university group
             if any(kw in text for kw in ['جامعة', 'كلية', 'تخصص', 'دفعة', 'استفسارات']):
                 sample['labels'] = ['Normal']
                 sample['label'] = 'Normal'
                 sample['note'] = f"Auto-Fix: Reverted to Normal (Legitimate Group) [Originally Academic]"
                 sample['reviewed_at'] = datetime.now().isoformat()
                 legit_fix_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Added 'Medical Fraud' to {med_fix_count} samples.")
    print(f"✅ Reverted {legit_fix_count} legitimate groups to 'Normal'.")

if __name__ == "__main__":
    main()
