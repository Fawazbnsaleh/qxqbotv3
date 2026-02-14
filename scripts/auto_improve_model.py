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
SOURCE_DIR = "data/telethonSamples"

# "Oracle" strict rules to auto-label caught gaps
ORACLE_RULES = {
    "Financial Scams": [
        re.compile(r"(قرض|تمويل).{0,30}(بدون.*كفيل|سداد.*مبكر|صندوق.*تنمية)", re.IGNORECASE),
        re.compile(r"استخراج.*قرض", re.IGNORECASE),
        re.compile(r"تسديد.*قروض", re.IGNORECASE),
    ],
    "Academic Cheating": [
        re.compile(r"حل.*(واجب|اختبار|اسايمنت)", re.IGNORECASE),
        re.compile(r"اعداد.*بحوث", re.IGNORECASE),
    ],
    "Medical Fraud": [
        re.compile(r"(سكليف|اجازة).*مرضية.*(قديم|جديد)", re.IGNORECASE),
        re.compile(r"عذر.*طبي.*مختم", re.IGNORECASE),
    ],
    "Hacking": [
        re.compile(r"(تهكير|اختراق).*(واتس|سناب|حساب)", re.IGNORECASE),
        re.compile(r"فك.*حظر.*(انستا|سناب)", re.IGNORECASE),
    ],
    "Spam": [
        re.compile(r"زيادة.*متابعين", re.IGNORECASE),
        re.compile(r"شحن.*(شدات|جواهر)", re.IGNORECASE),
    ]
}

# "Safe" markers to avoid labeling innocent questions as violations
SAFE_MARKERS = [
    re.compile(r"^(السلام عليكم)?\s*(ممكن|بسأل|استفسار|عندي|كيف|هل|وين)", re.IGNORECASE),
    re.compile(r"\?", re.IGNORECASE),
    re.compile(r"(حد|احد).*(يعرف|جرب)", re.IGNORECASE),
]

def load_random_batch(k=2000):
    files = glob.glob(os.path.join(SOURCE_DIR, "*.json"))
    messages = []
    print(f"Loading random batch from {len(files)} files...")
    
    selected_files = np.random.choice(files, min(len(files), 10), replace=False)
    
    for fpath in selected_files:
        if "_metadata.json" in fpath: continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                msgs = data if isinstance(data, list) else data.get('messages', [])
                for m in msgs:
                    txt = m.get('message') or m.get('text')
                    if txt and 10 < len(txt) < 500:
                        messages.append(txt)
        except: pass
        
    if len(messages) > k:
        return np.random.choice(messages, k, replace=False)
    return messages

def oracle_label(text):
    # Oracle Simulation: Decides the TRUE label based on strict regexes
    
    # 1. Is it definitely innocent?
    # Normalize for regex check? No, regexes are loose.
    # But checking 'question' markers is good.
    if any(p.search(text) for p in SAFE_MARKERS):
         # It's a question. Even if it has "loans", it's likely "How do I get a loan?" -> Normal
         return "Normal"

    # 2. Check violations
    for cat, patterns in ORACLE_RULES.items():
        if any(p.search(text) for p in patterns):
            return cat
            
    return None # Oracle is unsure, skip this sample

def run_loop(iterations=3):
    for i in range(1, iterations + 1):
        print(f"\n=== Iteration {i}/{iterations} ===")
        
        # 1. Train current model
        print("Training model...")
        # Since we are running from qxqbotv3 root, and train.py is inside al_rased/features/model/
        # and venv is inside al_rased/venv
        cmd = "source al_rased/venv/bin/activate && python3 al_rased/features/model/train.py"
        ret = os.system(cmd)
        if ret != 0:
            print("Training failed! stopping.")
            break
        
        # 2. Load Model
        try:
            clf = joblib.load(MODEL_FILE)
        except:
            print("Model not found, skipping.")
            return

        # 3. Mine Gaps
        candidates = load_random_batch(3000)
        print(f"Mining {len(candidates)} candidates for logical gaps...")
        
        norm_candidates = [normalize_text(txt) for txt in candidates]
        
        # Predict Probabilities
        probs = clf.predict_proba(norm_candidates)
        preds = clf.predict(norm_candidates)
        classes = clf.classes_
        
        new_samples = []
        
        for idx, text in enumerate(candidates):
            pred_label = preds[idx]
            prob = np.max(probs[idx])
            
            # Logic A: High Confidence Violation? (Check if it matches Oracle, if so, ignore - model is good)
            # Logic B: High Confidence Normal BUT Oracle says Violation? (FALSE NEGATIVE - CRITICAL)
            # Logic C: Low Confidence? (UNCERTAIN)
            
            true_label = oracle_label(text)
            
            if true_label:
                # Case 1: Model Missed it (False Negative)
                if pred_label == "Normal" and true_label != "Normal":
                    new_samples.append({
                        "text": text,
                        "label": true_label,
                        "reason": f"False Negative (Model: Normal, Oracle: {true_label})"
                    })
                
                # Case 2: Model says Violation, Oracle says Normal (False Positive - detected by safe markers)
                elif pred_label != "Normal" and true_label == "Normal":
                     new_samples.append({
                        "text": text,
                        "label": "Normal",
                        "reason": f"False Positive (Model: {pred_label}, Oracle: Normal)"
                    })

                # Case 3: Uncertain (0.4 - 0.7) and Oracle knows the answer
                elif 0.4 < prob < 0.7:
                    new_samples.append({
                        "text": text,
                        "label": true_label,
                        "reason": f"Uncertain ({prob:.2f})"
                    })
                    
        print(f"Identified {len(new_samples)} new hard samples.")
        
        if not new_samples:
            print("No gaps found this iteration. Stopping early.")
            break
            
        # 4. Add to Dataset
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
            
        existing_texts = {d['text'] for d in current_data}
        added = 0
        for s in new_samples:
            if s['text'] not in existing_texts:
                current_data.append({
                    "text": s['text'],
                    "label": s['label'],
                    "reviewed_by": "active_learning_loop",
                    "note": s['reason']
                })
                existing_texts.add(s['text'])
                added += 1
                
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
            
        print(f"Added {added} unique samples to dataset.")

if __name__ == "__main__":
    run_loop()
