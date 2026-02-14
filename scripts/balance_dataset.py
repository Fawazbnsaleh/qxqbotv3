import json
import random

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"

def balance_dataset():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Count classes
    params = {}
    for d in data:
        label = d['label']
        params[label] = params.get(label, 0) + 1
        
    print("Current Distribution:", params)
    
    # Target: Make minimal classes at least 150 (matches Academic Cheating)
    TARGET_MIN = 150
    
    new_data = list(data)
    
    for label, count in params.items():
        if count < TARGET_MIN and label != "طبيعي":
            # Oversample
            needed = TARGET_MIN - count
            print(f"Oversampling {label}: Adding {needed} copies...")
            
            # Get samples of this class
            samples = [d for d in data if d['label'] == label]
            
            for _ in range(needed):
                # Pick a random sample and duplicate it
                # Slight variation? No, exact duplication works for simple models to upweight
                dup = random.choice(samples).copy()
                dup['note'] = "Oversampling clone"
                new_data.append(dup)
                
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
        
    print("Dataset balanced.")

if __name__ == "__main__":
    balance_dataset()
