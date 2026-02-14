"""
Targeted Mining for Spam and Financial Scams categories.
"""
import sys
import os
import json
import glob
import re
import joblib
import random

sys.path.append(os.path.join(os.getcwd(), 'al_rased'))
from core.utils.text import normalize_text

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"
MODEL_FILE = "al_rased/features/model/classifier.joblib"
SOURCE_DIRS = [
    "/Users/apple/qxqbotv3/data/telethonSamples",
    "/Users/apple/qxqbotv3/data/telethonSamplesv2"
]

# Aggressive patterns for target categories
PATTERNS = {
    "Spam": [
        re.compile(r"(شحن|متجر|رشق|زيادة).*?(شدات|متابعين|لايكات|نجوم)", re.IGNORECASE),
        re.compile(r"(قسائم|كوبون|خصم).*?(نون|امازون|شي ان)", re.IGNORECASE),
        re.compile(r"(فورت|ببجي|فري فاير|تيك توك).*?(شحن|رصيد|جواهر)", re.IGNORECASE),
        re.compile(r"(اشتراك|باقة).*?(نتفلكس|شاهد|spotify)", re.IGNORECASE),
    ],
    "Financial Scams": [
        re.compile(r"(قرض|تمويل|سلفة).*?(بدون كفيل|فوري|سريع)", re.IGNORECASE),
        re.compile(r"(تصفير|استخراج).*?(مديونية|قروض|ضريبة)", re.IGNORECASE),
        re.compile(r"(سعوده|وظيفة).*?(راتب بدون عمل|تسجيل تأمينات)", re.IGNORECASE),
        re.compile(r"(استثمار|ربح).*?(يومي|مضمون|دولار)", re.IGNORECASE),
    ]
}

def load_messages():
    messages = []
    seen = set()
    for s_dir in SOURCE_DIRS:
        files = glob.glob(os.path.join(s_dir, "*.json"))
        for fpath in files:
            if "_metadata.json" in fpath: continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    msgs = data if isinstance(data, list) else data.get('messages', [])
                    for m in msgs:
                        txt = m.get('message') or m.get('text')
                        if txt and 15 < len(txt) < 800 and txt not in seen:
                            messages.append(txt)
                            seen.add(txt)
            except: pass
    return messages

def run_targeted_mining():
    print("Loading model...")
    clf = joblib.load(MODEL_FILE)
    
    print("Loading messages...")
    messages = load_messages()
    print(f"Scanning {len(messages)} messages for Spam and Financial Scams...")
    
    new_samples = []
    
    # Batch processing
    batch_size = 5000
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i+batch_size]
        norm_batch = [normalize_text(m) for m in batch]
        preds = clf.predict(norm_batch)
        
        for idx, text in enumerate(batch):
            pred_label = preds[idx]
            norm_text = norm_batch[idx]
            
            # Check if matches target patterns
            matched_cat = None
            for cat, patterns in PATTERNS.items():
                if any(p.search(norm_text) for p in patterns):
                    matched_cat = cat
                    break
            
            if matched_cat:
                if pred_label == "Normal":
                    # FALSE NEGATIVE
                    new_samples.append({
                        "text": text,
                        "label": matched_cat,
                        "reason": f"Targeted Mining: False Negative"
                    })
                elif pred_label != matched_cat:
                    # WRONG CATEGORY
                    new_samples.append({
                        "text": text,
                        "label": matched_cat,
                        "reason": f"Targeted Mining: Wrong Category (was {pred_label})"
                    })
    
    print(f"Found {len(new_samples)} samples for target categories.")
    
    if not new_samples:
        print("No new samples found for Spam/Financial Scams.")
        return
    
    # Add to training data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    
    existing_texts = {d['text'] for d in training_data}
    added = {"Spam": 0, "Financial Scams": 0}
    
    random.shuffle(new_samples)
    
    for s in new_samples:
        if s['text'] not in existing_texts:
            training_data.append({
                "text": s['text'],
                "label": s['label'],
                "reviewed_by": "targeted_miner",
                "note": s['reason']
            })
            existing_texts.add(s['text'])
            added[s['label']] = added.get(s['label'], 0) + 1
            
            # Limit per category
            if added["Spam"] >= 100 and added["Financial Scams"] >= 100:
                break
    
    print(f"Added: Spam={added['Spam']}, Financial Scams={added['Financial Scams']}")
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)
    
    print("Dataset updated.")

if __name__ == "__main__":
    run_targeted_mining()
