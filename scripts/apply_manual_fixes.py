
import json
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("✍️ Applying Manual Fixes...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Manual Corrections List
    # Format: {'index': I, 'new_label': L, 'reason': R}
    fixes = [
        {'index': 2303, 'new_label': 'Spam', 'reason': 'Selling laptop (Ad)'},
        {'index': 2331, 'new_label': 'Spam', 'reason': 'Promoting driver service (Ad)'},
        {'index': 2345, 'new_label': 'Financial Scams', 'reason': 'Promise of daily returns (Scam)'},
        {'index': 2387, 'new_label': 'Academic Cheating', 'reason': 'Offering homework services (Cheating)'},
        {'index': 2446, 'new_label': 'Spam', 'reason': 'Selling gaming laptop (Ad)'},
        {'index': 2519, 'new_label': 'Spam', 'reason': 'Game server promotion'},
        {'index': 2554, 'new_label': 'Spam', 'reason': 'Game server promotion'},
        {'index': 2563, 'new_label': 'Spam', 'reason': 'Affiliate/Promo link'}
    ]

    for fix in fixes:
        idx = fix['index']
        if idx < len(data):
            sample = data[idx]
            old_label = sample.get('label', 'Normal')
            
            sample['label'] = fix['new_label']
            sample['labels'] = [fix['new_label']]
            sample['note'] = f"Manual Fix: {fix['reason']} (was {old_label})"
            sample['reviewed_at'] = datetime.now().isoformat()
            
            print(f"✅ Fixed [{idx}]: {fix['new_label']} (was {old_label})")

    # Save
    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✨ Applied {len(fixes)} manual corrections.")

if __name__ == "__main__":
    main()
