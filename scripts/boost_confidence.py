"""
Confidence Boosting Script.
Addresses low confidence by:
1. Reducing Normal class to balance with violations
2. Oversampling high-quality violations
3. Tuning classifier for better class separation
"""
import json
import random
import os
import sys

sys.path.append(os.path.join(os.getcwd(), 'al_rased'))

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"

def balance_for_confidence():
    print("=" * 60)
    print("CONFIDENCE BOOSTING - PHASE 1: BALANCING CLASSES")
    print("=" * 60)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Group by label
    by_label = {}
    for d in data:
        label = d['label']
        if label not in by_label:
            by_label[label] = []
        by_label[label].append(d)
    
    print("\nCurrent distribution:")
    for label, samples in sorted(by_label.items(), key=lambda x: -len(x[1])):
        print(f"  {label}: {len(samples)}")
    
    # Problem: Normal (1746) >> Others (129-532)
    # Solution: Reduce Normal and Oversample violations
    
    # Step 1: Reduce Normal to match largest violation class
    normal_samples = by_label.get('Normal', [])
    max_violation_count = max(len(s) for l, s in by_label.items() if l != 'Normal')
    
    # Keep Normal at 1.5x the max violation (not 3x)
    target_normal = int(max_violation_count * 1.5)
    
    if len(normal_samples) > target_normal:
        print(f"\nReducing Normal from {len(normal_samples)} to {target_normal}...")
        random.shuffle(normal_samples)
        by_label['Normal'] = normal_samples[:target_normal]
    
    # Step 2: Oversample violations to reach target
    target_violation = max_violation_count
    
    for label in by_label:
        if label == 'Normal':
            continue
        
        samples = by_label[label]
        if len(samples) < target_violation:
            needed = target_violation - len(samples)
            print(f"Oversampling {label}: Adding {needed} copies...")
            
            # Duplicate random samples
            for _ in range(needed):
                dup = random.choice(samples).copy()
                dup['note'] = 'Confidence boost clone'
                by_label[label].append(dup)
    
    # Rebuild dataset
    new_data = []
    for label, samples in by_label.items():
        new_data.extend(samples)
    
    random.shuffle(new_data)
    
    print("\nNew distribution:")
    new_counts = {}
    for d in new_data:
        new_counts[d['label']] = new_counts.get(d['label'], 0) + 1
    for label, count in sorted(new_counts.items()):
        print(f"  {label}: {count}")
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal samples: {len(new_data)}")
    return len(new_data)

if __name__ == "__main__":
    balance_for_confidence()
