
import json
import re
import os
import sys
from collections import Counter

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔥 Running Stress Test (Obfuscation & Fuzzy Duplicates)...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # 1. Spaced Obfuscation Check (e.g. "ح ل و ا ج ب")
    # We look for single letters separated by spaces that form keywords
    print("\n1️⃣ Detecting Spaced Keywords...")
    
    keywords = [
        ('حل واجب', r'ح\s*ل\s+و\s*ا\s*ج\s*ب'),
        ('تهكير', r'ت\s*ه\s*ك\s*ي\s*ر'),
        ('استثمار', r'ا\s*س\s*ت\s*ث\s*م\s*ا\s*r'),
        ('سكس', r'س\s*ك\s*س'),
        ('نودز', r'ن\s*و\s*d\s*z')
    ]
    
    spaced_matches = []
    
    for i, sample in enumerate(data):
        text = sample['text']
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        
        # Only care if label is Normal or Spam
        if 'Normal' in labels or 'Spam' in labels:
            for kw, pattern in keywords:
                # Find spaced pattern (at least 2 spaces to be suspicious)
                matches = re.findall(pattern, text)
                if matches:
                    # Check if it actually has spaces
                    if any(m.count(' ') >= 2 for m in matches):
                        spaced_matches.append({
                            'text': text[:50],
                            'found': kw,
                            'label': labels
                        })

    print(f"   Found {len(spaced_matches)} obfuscated samples.")
    if spaced_matches:
        for m in spaced_matches[:5]:
            print(f"   - Found '{m['found']}' in {m['label']}: {m['text']}...")


    # 2. Fuzzy Duplicates (Diff < 5 chars)
    print("\n2️⃣ Detecting Fuzzy Duplicates...")
    
    # Simple hash based on first 50 chars + length (optimization)
    sim_map = {}
    fuzzy_count = 0
    
    for i, sample in enumerate(data):
        text = sample['text'].strip()
        # Simplified key: first 30 chars normalized
        key = re.sub(r'\s+', '', text[:30])
        
        if key in sim_map:
            # Check length diff
            other_text = sim_map[key]['text']
            if abs(len(text) - len(other_text)) < 10:
                # Calculate simple similarity ratio
                # (Levenshtein is heavy, simple overlap check)
                fuzzy_count += 1
        else:
            sim_map[key] = {'text': text, 'id': i}
            
    # Note: We already removed exact duplicates. High fuzzy count could mean legitimate templates or spam templates.
    print(f"   Found ~{fuzzy_count} potential fuzzy duplicates (templates).")


    # 3. Class Health Check
    print("\n3️⃣ Class Health Check (Avg Length)...")
    stats = {}
    for sample in data:
         labels = sample.get('labels', [sample.get('label')])
         for l in labels:
             if l not in stats: stats[l] = []
             stats[l].append(len(sample['text']))
             
    print(f"| {'Label':<20} | {'Count':<6} | {'Avg Len':<8} | {'Min Len':<8} |")
    print("|" + "-"*22 + "|" + "-"*8 + "|" + "-"*10 + "|" + "-"*10 + "|")
    
    for label, lens in stats.items():
        avg = sum(lens)/len(lens)
        print(f"| {label:<20} | {len(lens):<6} | {avg:<8.1f} | {min(lens):<8} |")
        
    # Check for suspiciously short Normal messages
    short_normal = [s for s in data if 'Normal' in s.get('labels', []) and len(s['text']) < 15]
    print(f"\n4️⃣ Short Normal Messages (<15 chars): {len(short_normal)}")
    if short_normal:
        print("   Examples:")
        for s in short_normal[:5]:
             print(f"   - '{s['text']}'")

if __name__ == "__main__":
    main()
