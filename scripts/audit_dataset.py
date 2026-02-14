import json
import random
import sys
import os

sys.path.append(os.getcwd())

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"

def audit_data():
    if not os.path.exists(DATA_FILE):
        print("Data file not found.")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total samples: {len(data)}")
    
    by_category = {}
    for item in data:
        cat = item['label']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    print("\n--- Category Distribution ---")
    for cat, items in by_category.items():
        print(f"{cat}: {len(items)}")

    print("\n--- Random Spot Check (5 per category) ---")
    for cat, items in by_category.items():
        print(f"\n[Category: {cat}]")
        samples = random.sample(items, min(len(items), 5))
        for s in samples:
            print(f"- ({s.get('reviewed_by', 'unknown')}): {s['text'][:100]}...")

if __name__ == "__main__":
    audit_data()
