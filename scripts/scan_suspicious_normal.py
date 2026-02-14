
import json
import re
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔍 Scanning for Suspicious 'Normal' Samples...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    suspicious_keywords = [
        'سعر', 'خاص', 'تواصل', 'متوفر', 'عرض', 'خصم', 'اشتراك', 'بيع', 'شراء', 
        'حساب', 'بطاقة', 'رصيد', 'تحويل', 'بنك', 'صراف', 'فلوس', 'ريال', 'دولار'
    ]

    suspicious_samples = []
    
    for i, sample in enumerate(data):
        text = sample['text']
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        if isinstance(labels, str): labels = [labels]

        # Only check Normal samples
        if 'Normal' in labels and len(labels) == 1:
            # Check for short, ad-like messages
            if len(text) < 200: 
                matches = [kw for kw in suspicious_keywords if kw in text]
                if matches:
                    suspicious_samples.append({
                        'index': i,
                        'text': text,
                        'matches': matches
                    })

    print(f"found {len(suspicious_samples)} suspicious Normal samples.")
    print("-" * 50)
    
    # Print first 20 for manual inspection
    for s in suspicious_samples[:50]:
        print(f"[{s['index']}] Matches: {s['matches']}")
        print(f"Text: {s['text']}")
        print("-" * 30)

if __name__ == "__main__":
    main()
