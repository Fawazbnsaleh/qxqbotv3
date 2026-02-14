
import json
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🌍 Arabizing Dataset Labels...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    backup_path = 'al_rased/data/labeledSamples/training_data_english.json'
    
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Backup
    with open(backup_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"   Backup saved to {backup_path}")

    mapping = {
        'Normal': 'طبيعي',
        'Spam': 'سبام',
        'Academic Cheating (Offer)': 'غش أكاديمي (عرض)',
        'Academic Cheating (Request)': 'غش أكاديمي (طلب)',
        'Medical Fraud (Offer)': 'احتيال طبي (عرض)',
        'Medical Fraud (Request)': 'احتيال طبي (طلب)',
        'Financial Scams (Offer)': 'احتيال مالي (عرض)',
        'Financial Scams (Request)': 'احتيال مالي (طلب)',
        'Hacking (Offer)': 'تهكير (عرض)',
        'Hacking (Request)': 'تهكير (طلب)',
        'Unethical (Offer)': 'غير أخلاقي (عرض)',
        'Unethical (Request)': 'غير أخلاقي (طلب)',
        
        # Retroactive fixes for missed categories if any
        'Academic Cheating': 'غش أكاديمي (عرض)', 
        'Medical Fraud': 'احتيال طبي (عرض)',
        'Financial Scams': 'احتيال مالي (عرض)',
        'Hacking': 'تهكير (عرض)',
        'Unethical': 'غير أخلاقي (عرض)'
    }

    count = 0
    for sample in data:
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        new_labels = []
        modified = False
        
        for l in labels:
            if l in mapping:
                new_labels.append(mapping[l])
                modified = True
            else:
                new_labels.append(l) # Keep as is if not in map (should not happen)
        
        if modified:
            sample['labels'] = new_labels
            sample['label'] = new_labels[0]
            count += 1
            
    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Arabized {count} samples.")

if __name__ == "__main__":
    main()
