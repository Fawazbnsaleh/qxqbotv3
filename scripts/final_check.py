
import json
import re
import os
import sys
from collections import Counter

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🛡️ Starting Final Rigorous Consistency Check...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # 1. Duplicates Check
    seen_texts = {}
    duplicates = []
    for i, d in enumerate(data):
        text = d['text'].strip()
        if text in seen_texts:
            duplicates.append((i, seen_texts[text]))
        seen_texts[text] = i
    
    print(f"\n1️⃣ Duplicates: {len(duplicates)} found.")

    # 2. Label Validity Check
    VALID_LABELS = {
        'Normal', 'Academic Cheating', 'Medical Fraud', 'Financial Scams', 
        'Hacking', 'Spam', 'Unethical'
    }
    invalid_labels = []
    for i, d in enumerate(data):
        labels = d.get('labels', [])
        for l in labels:
            if l not in VALID_LABELS:
                invalid_labels.append(l)
    
    print(f"2️⃣ Invalid Labels: {len(invalid_labels)} found.")

    # 3. Garbage / Noise Check in Normal
    garbage_normal = []
    english_normal = []
    
    for i, d in enumerate(data):
        labels = d.get('labels', [])
        text = d['text']
        
        if 'Normal' in labels:
            # Short garbage
            if len(text) < 10:
                garbage_normal.append(text)
            
            # English Spam disguised as Normal?
            # If text is > 80% English letters and length > 50
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            if len(text) > 50 and (english_chars / len(text)) > 0.8:
                english_normal.append(text[:50])

    print(f"3️⃣ Garbage 'Normal' (<10 chars): {len(garbage_normal)}")
    print(f"4️⃣ Suspicious English 'Normal': {len(english_normal)}")

    # 4. Strict Keyword Re-Verification
    VIOLATION_KEYWORDS = {
        'حل واجب': 'Academic Cheating',
        'سكليف': 'Medical Fraud',
        'استثمار': 'Financial Scams', # Can be Normal but rare
        'تهكير': 'Hacking',
        'ممحون': 'Unethical'
    }
    
    violations = []
    for i, d in enumerate(data):
        labels = d.get('labels', [])
        text = d['text']
        
        if 'Normal' in labels and len(labels) == 1:
            for kw, cat in VIOLATION_KEYWORDS.items():
                if kw in text:
                    # Exception for "استثمار" if context is valid (checked before, but let's see)
                    if kw == 'استثمار' and ('بنك' in text or 'حلال' in text):
                        continue
                    violations.append({'text': text[:40], 'found': kw, 'should_be': cat})

    print(f"5️⃣ Remaining Keyword Violations in 'Normal': {len(violations)}")
    if violations:
        print("   Examples:")
        for v in violations:
            print(f"   - Found '{v['found']}' -> Should be {v['should_be']}: {v['text']}...")

    # 5. Missing Fields
    missing_fields = [i for i, d in enumerate(data) if 'labels' not in d]
    print(f"6️⃣ Samples missing 'labels' field: {len(missing_fields)}")

if __name__ == "__main__":
    main()
