
import json
import re
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🌿 Auditing 'Normal' Samples for Subtle Spam...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    normal_samples = [d for d in data if 'Normal' in d.get('labels', [d.get('label')])]
    print(f"Total Normal Samples: {len(normal_samples)}")
    
    suspicious = []
    
    # regex for phone numbers (SA)
    phone_re = r'(05\d{8}|5\d{8}|\+9665\d{8})'
    # regex for URLs
    url_re = r'(https?://|t\.me/)'
    # regex for usernames
    user_re = r'@[a-zA-Z0-9_]+'

    for i, sample in enumerate(normal_samples):
        text = sample['text']
        
        reasons = []
        
        # 1. Check for Phone Numbers
        if re.search(phone_re, text):
            reasons.append("Phone Number")
            
        # 2. Check for URLs
        if re.search(url_re, text):
            reasons.append("URL")
            
        # 3. Check for Usernames
        if re.search(user_re, text):
             # Only flag if it also has "private" or "dm" keywords
             if any(kw in text for kw in ['خاص', 'تواصل', 'dm', 'pv']):
                 reasons.append("Username + Contact")
        
        # 4. Check for Invite/Join keywords
        if any(kw in text for kw in ['انضم', 'رابط المجموعة', 'حياكم', 'قروبنا']):
            reasons.append("Invite/Join")

        if reasons:
            suspicious.append({
                'text': text[:60],
                'reason': ", ".join(reasons)
            })

    print(f"\n⚠️ Suspicious Normal Samples: {len(suspicious)}")
    
    # Print a sample
    print("\nExamples:")
    for s in suspicious[:40]:
        print(f"   - [{s['reason']}] {s['text']}...")

if __name__ == "__main__":
    main()
