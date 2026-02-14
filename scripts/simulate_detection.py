import sys
import os
import json
import glob
import re
import pandas as pd
import numpy as np

# Setup paths to import from al_rased
sys.path.append(os.path.abspath("al_rased"))

from features.detection.engine import DetectionEngine
from core.utils.text import normalize_text

SOURCE_DIR = "/Users/apple/qxqbotv3/data/telethonSamples"
OUTPUT_JSON = "al_rased/data/results/simulation_v1_aggressive.json"
OUTPUT_TXT = "al_rased/data/results/simulation_v1_aggressive_summary.txt"

# Oracle Keywords for "Gap Analysis" (What we expect to be caught)
ORACLE_PATTERNS = {
    "Financial Scams": [r"قرض", r"تمويل", r"سداد", r"بنك التسليف", r"بدون كفيل"],
    "Academic Cheating": [r"حل واجب", r"اعداد بحث", r"مشروع تخرج", r"اسايمنت"],
    "Medical Fraud": [r"سكليف", r"طبي", r"مرضية", r"صحتي"],
    "Hacking": [r"تجسس", r"اختراق", r"هكر", r"استرجاع حساب"],
    "Spam": [r"زيادة متابعين", r"اشتراك", r"فورت نايت", r"شحن"]
}

def load_all_messages(limit=5000):
    files = glob.glob(os.path.join(SOURCE_DIR, "*.json"))
    messages = []
    print(f"Scanning {len(files)} files...")
    
    # Shuffle files to get random distribution
    random.shuffle(files)
    
    for fpath in files:
        if "_metadata.json" in fpath: continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                msgs = data if isinstance(data, list) else data.get('messages', [])
                for m in msgs:
                    txt = m.get('message') or m.get('text')
                    if txt and 10 < len(txt) < 1000:
                        messages.append(txt)
                        if len(messages) >= limit:
                            return messages
        except: pass
    return messages

import random

def run_simulation():
    # 1. Load Model
    print("Loading Detection Engine...")
    DetectionEngine.load_model()
    
    # 2. Load Data
    messages = load_all_messages(10000)
    print(f"Simulating on {len(messages)} raw messages...")
    
    results = []
    stats = {"Total": 0, "Violations": 0, "Normal": 0, "Missed_Likely": 0}
    
    print("Running detection...")
    for text in messages:
        stats["Total"] += 1
        
        # Actual Bot Prediction
        prediction = DetectionEngine.predict(text)
        
        # Oracle Check (Did it MISS something obvious?)
        likely_violation_category = None
        if prediction == "Normal":
            for cat, keywords in ORACLE_PATTERNS.items():
                for kw in keywords:
                    if re.search(kw, text):
                         # It contains a suspicious keyword but model said Normal.
                         # This implies either a False Negative OR Correctly identified as Innocent Question.
                         likely_violation_category = cat
                         break
                if likely_violation_category: break
        
        item = {
            "text": text,
            "prediction": prediction,
            "missed_oracle_category": likely_violation_category
        }
        
        if prediction != "Normal":
            stats["Violations"] += 1
            results.append(item) # Keep all violations
        else:
            stats["Normal"] += 1
            if likely_violation_category:
                 stats["Missed_Likely"] += 1
                 results.append(item) # Keep "Missed" candidates for review
            # We don't keep pure Normal-Normal to save space
            
    # 3. Save Results
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    # 4. Generate Report
    report = []
    report.append(f"Simulation Analysis on {stats['Total']} messages")
    report.append("="*40)
    report.append(f"Total Violations Detected: {stats['Violations']} ({stats['Violations']/stats['Total']:.1%})")
    report.append(f"Potential Misses (False Negatives): {stats['Missed_Likely']} ({stats['Missed_Likely']/stats['Total']:.1%})")
    
    # Breakdown of Detections
    df = pd.DataFrame(results)
    if not df.empty:
        det_counts = df[df['prediction'] != 'Normal']['prediction'].value_counts()
        report.append("\nViolations by Category (Detected):")
        report.append(str(det_counts))
        
        miss_counts = df[df['prediction'] == 'Normal']['missed_oracle_category'].value_counts()
        report.append("\nPotential Misses by Category (Oracle Flagged):")
        report.append(str(miss_counts))
        
        report.append("\n--- Sample Misses (Review Needed) ---")
        misses = df[df['prediction'] == 'Normal'].sample(min(10, len(df[df['prediction'] == 'Normal'])))
        for _, row in misses.iterrows():
            report.append(f"[{row['missed_oracle_category']}] {row['text'][:100]}...")

    report_str = "\n".join(report)
    print(report_str)
    
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        f.write(report_str)

if __name__ == "__main__":
    run_simulation()
