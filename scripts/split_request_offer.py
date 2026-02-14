
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔄 Migrating Schema to Request/Offer split...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    backup_path = 'al_rased/data/labeledSamples/training_data_pre_split.json'
    
    with open(data_path, 'r') as f:
        data = json.load(f)
        
    # backup first
    with open(backup_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"   Backup saved to {backup_path}")

    # Heuristics
    re_request = re.compile(r'(ابغى|مين عنده|مطلوب|احتاج|بغيت|ابي|هل يوجد|ممكن|شخص|يساعدني|استفسار|بحث عن|اريد|مين يعرف|محتاج)', re.DOTALL)
    re_offer = re.compile(r'(متوفر|يوجد|لدينا|حياكم|عروض|خصم|تواصل|واتس|خاص|نقدم|خدمات|لحل|سعر|اشترك|للبيع|حسابات|انجاز|فوري)', re.DOTALL)

    cats_to_split = [
        'Academic Cheating', 
        'Medical Fraud', 
        'Financial Scams', 
        'Hacking', 
        'Unethical'
    ]
    
    migrated_count = 0
    
    for sample in data:
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        new_labels = []
        modified = False
        
        for label in labels:
            if label in cats_to_split:
                text = sample['text']
                is_req = re_request.search(text)
                is_off = re_offer.search(text)
                
                # Default logic:
                # If explicit Request -> Request
                # Everything else -> Offer (Safety default: Assume it's a service/violation unless explicitly just asking)
                # Exception: Medical Fraud, usually purely Offer.
                
                suffix = "(Offer)" # Default
                
                if is_req and not is_off:
                    suffix = "(Request)"
                
                # Special overrides
                if label == 'Financial Scams':
                    suffix = "(Offer)" # Almost always offers
                 
                new_label = f"{label} {suffix}"
                new_labels.append(new_label)
                modified = True
            else:
                new_labels.append(label)
        
        if modified:
            sample['labels'] = new_labels
            sample['label'] = new_labels[0]
            # sample['note'] = "Schema Migration" # Optional, maybe skip to save space
            migrated_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Migrated {migrated_count} samples to new schema.")

if __name__ == "__main__":
    main()
