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
SOURCE_DIR = "/Users/apple/qxqbotv3/data/telethonSamplesv2"

# STRICT ORACLE PATTERNS (Aggressive)
# If a text matches these, it IS a violation. No excuses.
AGGRESSIVE_RULES = {
    "احتيال طبي (عرض)": [
        re.compile(r"(سكليف|اجازة|تقرير|عذر).*?(مرضي|طبي).*?(للبيع|اصدار|تواريخ|قديمة|جديدة|معتمد|صحتي|مختم|الخرج)", re.IGNORECASE),
        re.compile(r"(ارفع|تنزل).*?(منصة|تطبيق).*?(صحتي)", re.IGNORECASE),
        re.compile(r"(سكليف|اجازه).*?(واتس|خاص|تواصل)", re.IGNORECASE),
    ],
    "غش أكاديمي (عرض)": [
        re.compile(r"(حل|اسوي|اعداد).*?(واجب|اختبار|بحث|مشروع|تكليف)", re.IGNORECASE),
        re.compile(r"(خدمات).*?(طلابية).*?(جامعية|ثانوي)", re.IGNORECASE),
    ],
    "احتيال مالي (عرض)": [
        re.compile(r"(قرض|تمويل|سداد).*?(بدون|فوري|ميسر)", re.IGNORECASE),
        re.compile(r"(استخراج|تصفير).*?(قرض|مديونية|ضريبة)", re.IGNORECASE),
    ],
    "تهكير (عرض)": [
        re.compile(r"(استرجاع|تهكير|اختراق).*?(حساب|سناب|واتس)", re.IGNORECASE),
    ],
     "سبام": [
        re.compile(r"(زيادة|دعم|رشق).*?(متابعين|لايكات)", re.IGNORECASE),
        re.compile(r"(شحن|متجر).*?(شدات|تيك توك)", re.IGNORECASE),
    ]
}

def load_data(limit=10000):
    files = glob.glob(os.path.join(SOURCE_DIR, "*.json"))
    messages = []
    print(f"Scanning {len(files)} files...")
    random.shuffle(files)
    for fpath in files:
        if "_metadata.json" in fpath: continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                msgs = data if isinstance(data, list) else data.get('messages', [])
                for m in msgs:
                    txt = m.get('message') or m.get('text')
                    if txt and len(txt) > 10:
                         messages.append(txt)
                         if len(messages) >= limit: return messages
        except: pass
    return messages

import random

def run_aggressive_tuning():
    # 1. Load current model
    print("Loading model...")
    try:
        clf = joblib.load(MODEL_FILE)
    except:
        print("Model failed to load.")
        return

    # 2. Mine False Negatives
    print("Mining messages...")
    messages = load_data(20000) # Deep scan
    
    new_samples = []
    
    norm_msgs = [normalize_text(m) for m in messages]
    preds = clf.predict(norm_msgs)
    
    print(f"Analyzing {len(messages)} messages for misses...")
    
    for idx, text in enumerate(messages):
        prediction = preds[idx]
        norm_text = norm_msgs[idx]
        
        # Only interested if Model says "Normal" (We want to catch misses)
        if prediction == "طبيعي":
            matched_cat = None
            for cat, patterns in AGGRESSIVE_RULES.items():
                for p in patterns:
                    if p.search(norm_text): # Check regex against normalized text for better catch
                        matched_cat = cat
                        break
                if matched_cat: break
            
            if matched_cat:
                # FOUND ONE! Model said Normal, Aggressive Rule said Violation.
                # TRUST THE RULE.
                new_samples.append({
                    "text": text, # Store original text
                    "label": matched_cat,
                    "model_said": "طبيعي",
                    "reason": "Aggressive Mining via Regex"
                })

    print(f"Found {len(new_samples)} missed violations (False Negatives).")
    
    if not new_samples:
        print("No new samples found. Model is already aggressive enough.")
        return

    # 3. Add to Dataset
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    
    existing_texts = {d['text'] for d in training_data}
    added_count = 0
    
    for s in new_samples:
        if s['text'] not in existing_texts:
            training_data.append({
                "text": s['text'],
                "label": s['label'],
                "reviewed_by": "aggressive_miner",
                "note": "Recovered from False Negative"
            })
            existing_texts.add(s['text'])
            added_count += 1
            
    print(f"Adding {added_count} unique samples to training data...")
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)
        
    print("Dataset updated. Please run training script manually or via command.")

if __name__ == "__main__":
    run_aggressive_tuning()
