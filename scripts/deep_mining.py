import sys
import os
import json
import glob
import re
import joblib
import pandas as pd
import numpy as np

# Setup paths
sys.path.append(os.path.join(os.getcwd(), 'al_rased'))
from core.utils.text import normalize_text

TRAIN_SCRIPT_PATH = "al_rased/features/model/train.py"
DATA_FILE = "al_rased/data/labeledSamples/training_data.json"
MODEL_FILE = "al_rased/features/model/classifier.joblib"
# Scan BOTH directories
SOURCE_DIRS = [
    "/Users/apple/qxqbotv3/data/telethonSamples",
    "/Users/apple/qxqbotv3/data/telethonSamplesv2"
]

# Patterns for specific tricky cases we want to force-feed the model
# Using strictly high-precision regexes
PATTERNS = {
    "Medical Fraud": [
        re.compile(r"(سكليف|اجازة|تقرير|عذر).*?(صحتي|تواريخ|قديم|جديد|معتمد|مختم)", re.IGNORECASE),
        re.compile(r"(ارفع|تنزل).*?(منصة|تطبيق).*?(صحتي)", re.IGNORECASE),
    ],
    "Academic Cheating": [
        re.compile(r"(حل|اسوي|اعداد).*?(واجب|اختبار|بحث|مشروع|تكليف|كويز)", re.IGNORECASE),
    ],
    "Financial Scams": [
        re.compile(r"(قرض|تمويل|سداد).*?(بدون|فوري|ميسر|استخراج|تصفير)", re.IGNORECASE)
    ],
    "Hacking": [
        re.compile(r"(تهكير|اختراق|تجسس).*?(سناب|واتس|انستا|حساب)", re.IGNORECASE)
    ]
}

SAFE_PATTERNS = [
    re.compile(r"(كيف|وش|شنو|يعني|ايش).*?(اطلع|اسوي|طريقة|حل)", re.IGNORECASE), # Questions
    re.compile(r"\?", re.IGNORECASE),
    re.compile(r"(احد|مين).*?(يعرف|جرب)", re.IGNORECASE)
]

def load_all_data():
    messages = []
    seen = set()
    print("Loading ALL messages...")
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

def run_deep_mining():
    # 1. Load Model
    print("Loading model...")
    try:
        clf = joblib.load(MODEL_FILE)
    except:
        print("Model failed to load.")
        return

    # 2. Scan Everything
    messages = load_all_data()
    print(f"Deep scanning {len(messages)} unique messages...")
    
    # Batch processing to avoid memory issues if huge
    batch_size = 5000
    new_samples = []
    
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i+batch_size]
        norm_batch = [normalize_text(m) for m in batch]
        
        # Predict Probabilities
        probs = clf.predict_proba(norm_batch)
        preds = clf.predict(norm_batch)
        classes = clf.classes_
        
        for idx, text in enumerate(batch):
            pred_label = preds[idx]
            max_prob = np.max(probs[idx])
            
            # CRITERIA:
            # 1. Low Confidence Normal (30-70%) -> Could be a subtle violation OR a hard normal
            # 2. Confident Normal but matches Regex -> False Negative
            
            matched_cat = None
            is_safe = False
            
            # Check Regex Rules
            for cat, patterns in PATTERNS.items():
                if any(p.search(norm_batch[idx]) for p in patterns):
                    matched_cat = cat
                    break
            
            # Check Safe Rules
            if any(p.search(norm_batch[idx]) for p in SAFE_PATTERNS):
                is_safe = True
                
            # Decision Logic
            if matched_cat and not is_safe:
                if pred_label == "Normal":
                    # FALSE NEGATIVE (Missed)
                    new_samples.append({
                        "text": text,
                        "label": matched_cat,
                        "reason": f"Deep Mine: False Negative (Conf {max_prob:.2f})"
                    })
                elif pred_label == matched_cat and max_prob < 0.85:
                    # LOW CONFIDENCE (Right label, but weak)
                    new_samples.append({
                        "text": text,
                        "label": matched_cat,
                        "reason": f"Deep Mine: Low Confidence Violation ({max_prob:.2f})"
                    })
            
            elif is_safe:
                if pred_label != "Normal":
                    # FALSE POSITIVE
                    new_samples.append({
                        "text": text,
                        "label": "Normal",
                        "reason": f"Deep Mine: False Positive ({pred_label})"
                    })
                elif pred_label == "Normal" and max_prob < 0.7:
                     # LOW CONFIDENCE NORMAL (Confused by safe words?)
                     new_samples.append({
                        "text": text,
                        "label": "Normal",
                        "reason": f"Deep Mine: Weak Normal ({max_prob:.2f})"
                    })

    print(f"Found {len(new_samples)} hard training samples.")
    
    if not new_samples:
        print("Model is solid. No gaps found.")
        return

    # 3. Add to Dataset (Limit to avoid flooding)
    # We prioritize distinct samples
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    
    existing_texts = {d['text'] for d in training_data}
    added_count = 0
    
    # Shuffle new samples to get variety if we have too many
    import random
    random.shuffle(new_samples)
    
    for s in new_samples:
        if s['text'] not in existing_texts:
            training_data.append({
                "text": s['text'],
                "label": s['label'],
                "reviewed_by": "deep_miner",
                "note": s['reason']
            })
            existing_texts.add(s['text'])
            added_count += 1
            if added_count >= 500: break # Limit additions per run
            
    print(f"Adding {added_count} unique hard samples to training data...")
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)
        
    print("Dataset updated.")

if __name__ == "__main__":
    run_deep_mining()
