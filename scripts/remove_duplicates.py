
import json
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🧹 Cleaning Duplicates...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    print(f"Original size: {len(data)}")

    # Deduplication logic: Keep the one with the most detailed info (e.g. reviewed_at or notes)
    unique_data = {}
    
    for d in data:
        text = d['text'].strip()
        
        if text not in unique_data:
            unique_data[text] = d
        else:
            # Overwrite if current one has more info/is newer
            existing = unique_data[text]
            
            # Prefer manually reviewed
            if 'Corrected' in d.get('note', '') and 'Corrected' not in existing.get('note', ''):
                 unique_data[text] = d
            # Prefer newer check
            elif d.get('reviewed_at', '') > existing.get('reviewed_at', ''):
                 unique_data[text] = d

    cleaned_list = list(unique_data.values())
    print(f"Cleaned size: {len(cleaned_list)}")
    print(f"Removed {len(data) - len(cleaned_list)} duplicates.")

    with open(data_path, 'w') as f:
        json.dump(cleaned_list, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
