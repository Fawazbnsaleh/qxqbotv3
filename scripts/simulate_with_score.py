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

SOURCE_DIR = "/Users/apple/qxqbotv3/data/telethonSamplesv2"
OUTPUT_JSON = "al_rased/data/results/simulation_v2_scored.json"
OUTPUT_TXT = "al_rased/data/results/simulation_v2_scored_summary.txt"

# Oracle Keywords (Gap Analysis)
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
    import random
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

def run_simulation():
    # 1. Load Model
    print("Loading Detection Engine...")
    DetectionEngine.load_model()
    
    # 2. Load Data
    messages = load_all_messages(10000)
    print(f"Simulating on {len(messages)} raw messages...")
    
    results = []
    stats = {
        "Total": 0, 
        "Violations": 0, 
        "Normal": 0, 
        "Missed_Likely": 0,
        "Avg_Confidence_Violations": [],
        "Avg_Confidence_Normal": []
    }
    
    print("Running detection...")
    for text in messages:
        stats["Total"] += 1
        
        # Actual Bot Prediction
        res = DetectionEngine.predict(text)
        prediction = res["label"]
        confidence = res["confidence"]
        
        item = {
            "text": text,
            "prediction": prediction,
            "confidence": confidence,
            "missed_oracle_category": None
        }
        
        likely_violation_category = None
        
        # Dynamic Thresholds (Mirroring handlers.py)
        THRESHOLDS = {
            "Medical Fraud": 0.45,
            "Academic Cheating": 0.55,
            "Hacking": 0.65,
            "Financial Scams": 0.65,
            "Spam": 0.65
        }
        threshold = THRESHOLDS.get(prediction, 0.60)
        
        # Apply Threshold Logic
        final_prediction = prediction
        if prediction != "Normal" and confidence < threshold:
            final_prediction = "Normal"
            
        if final_prediction == "Normal":
            stats["Avg_Confidence_Normal"].append(confidence)
            # Oracle Check
            for cat, keywords in ORACLE_PATTERNS.items():
                for kw in keywords:
                    if re.search(kw, text):
                         likely_violation_category = cat
                         break
                if likely_violation_category: break
                
            if likely_violation_category:
                 stats["Missed_Likely"] += 1
                 item["missed_oracle_category"] = likely_violation_category
                 results.append(item)
        else:
            stats["Violations"] += 1
            stats["Avg_Confidence_Violations"].append(confidence)
            results.append(item)
            
    # 3. Save Results
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    # 4. Generate Report
    avg_conf_viol = np.mean(stats["Avg_Confidence_Violations"]) if stats["Avg_Confidence_Violations"] else 0
    avg_conf_norm = np.mean(stats["Avg_Confidence_Normal"]) if stats["Avg_Confidence_Normal"] else 0

    report = []
    report.append(f"Simulation Analysis (With Confidence Scores) on {stats['Total']} messages")
    report.append("="*60)
    report.append(f"Total Violations Detected: {stats['Violations']} ({stats['Violations']/stats['Total']:.1%})")
    report.append(f"  -> Average Confidence: {avg_conf_viol:.1%}")
    report.append("-" * 40)
    report.append(f"Potential Misses (False Negatives): {stats['Missed_Likely']} ({stats['Missed_Likely']/stats['Total']:.1%})")
    report.append("-" * 40)
    report.append(f"Average Confidence for Normal Decisions: {avg_conf_norm:.1%}")
    report.append("="*60)
    
    # Detailed Breakdown
    df = pd.DataFrame(results)
    if not df.empty and 'prediction' in df.columns:
        viol_df = df[df['prediction'] != 'Normal']
        if not viol_df.empty:
            report.append("\nConfidence by Category:")
            for cat in viol_df['prediction'].unique():
                sub = viol_df[viol_df['prediction'] == cat]
                report.append(f"- {cat.ljust(20)} Count: {len(sub)} | Avg Conf: {sub['confidence'].mean():.1%} | Min Conf: {sub['confidence'].min():.1%}")

        if 'missed_oracle_category' in df.columns:
             miss_counts = df[df['prediction'] == 'Normal']['missed_oracle_category'].value_counts()
             report.append("\nPotential Misses by Category:")
             report.append(str(miss_counts))

        report.append("\n--- Sample Violations (High Confidence) ---")
        high_conf = viol_df.nlargest(5, 'confidence')
        for _, row in high_conf.iterrows():
            report.append(f"[{row['prediction']} - {row['confidence']:.0%}] {row['text'][:80]}...")
            
        report.append("\n--- Sample Misses (Low Confidence Normal?) ---")
        # Check missed items
        missed_df = df[(df['prediction'] == 'Normal') & (df['missed_oracle_category'].notna())]
        if not missed_df.empty:
             sample_missed = missed_df.sample(min(5, len(missed_df)))
             for _, row in sample_missed.iterrows():
                 # High confidence Normal means model was SURE it's safe. Low means it was confused.
                 report.append(f"[Missed {row['missed_oracle_category']} - Model Confident Safe: {row['confidence']:.0%}] {row['text'][:80]}...")

    report_str = "\n".join(report)
    print(report_str)
    
    with open(OUTPUT_TXT, 'w', encoding='utf-8') as f:
        f.write(report_str)

if __name__ == "__main__":
    run_simulation()
