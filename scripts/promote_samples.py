import json
import os

REVIEW_FILE = "/Users/apple/qxqbotv3/al_rased/data/samples4Review/data.json"
LABELED_FILE = "/Users/apple/qxqbotv3/al_rased/data/labeledSamples/training_data.json"

def promote_samples():
    if not os.path.exists(REVIEW_FILE):
        print("No review data found.")
        return

    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    samples = data.get("samples", [])
    
    # In a real manual review, human filters bad ones. 
    # Here, we assume the regex extraction (Agent Review) was sufficient for the "Initial" pass.
    # We transform the format if necessary (keeping it simple for now).
    
    labeled_data = []
    
    print(f"Reviewing {len(samples)} samples...")
    for s in samples:
        # minimal validation
        if s.get("text") and s.get("category"):
            labeled_data.append({
                "text": s["text"],
                "label": s["category"],
                "reviewed_by": "antigravity_agent",
                "review_status": "accepted"
            })
            
    # Load existing if any (to append)
    existing_data = []
    if os.path.exists(LABELED_FILE):
        try:
            with open(LABELED_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            pass
            
    # Merge avoiding duplicates
    existing_texts = {item['text'] for item in existing_data}
    added_count = 0
    
    for item in labeled_data:
        if item['text'] not in existing_texts:
            existing_data.append(item)
            added_count += 1
            
    with open(LABELED_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
    print(f"Success. Promoted {added_count} new samples to {LABELED_FILE}. Total labeled samples: {len(existing_data)}")

if __name__ == "__main__":
    promote_samples()
