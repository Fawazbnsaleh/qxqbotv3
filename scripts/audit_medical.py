
import json
import re
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("⚕️ Auditing 'Medical Fraud' Samples...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    medical_samples = [d for d in data if 'Medical Fraud' in d.get('labels', [d.get('label')])]
    print(f"Total Medical Fraud Samples: {len(medical_samples)}")

    # Issues to look for:
    # 1. Missing 'Academic Cheating' label when both are present
    # 2. Legitimate medical questions (unlikely but possible)
    
    academic_kws = ['حل واجب', 'بحث', 'مشروع', 'تخرج', 'اختبار', 'كويز', 'اسايمنت']
    
    missing_academic = []
    suspicious_legit = []

    for i, sample in enumerate(medical_samples):
        text = sample['text']
        labels = sample.get('labels', [])
        
        # 1. Check for Academic overlap
        if any(kw in text for kw in academic_kws):
            if 'Academic Cheating' not in labels:
                missing_academic.append({'text': text[:60], 'id': i})

        # 2. Suspicious Legit (Questions about "How to get sick leave" vs "I sell sick leave")
        # If text doesn't have commercial keywords but asks "How?"
        if 'كيف' in text and not any(kw in text for kw in ['سعر', 'فلوس', 'تواصل', 'خاص', 'رقم']):
             suspicious_legit.append({'text': text[:60], 'id': i})

    print(f"\n⚠️ Missing 'Academic Cheating' Label: {len(missing_academic)}")
    for m in missing_academic[:10]:
        print(f"   - {m['text']}...")
        
    print(f"\n⚠️ Potential Legitimate Questions: {len(suspicious_legit)}")
    for m in suspicious_legit[:10]:
        print(f"   - {m['text']}...")

if __name__ == "__main__":
    main()
