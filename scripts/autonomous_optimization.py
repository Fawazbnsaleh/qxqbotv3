"""
Autonomous Model Optimization Pipeline.
Runs iterative mining, training, and testing until performance converges.
"""
import subprocess
import sys
import json
import os
import re
import random

sys.path.append(os.path.join(os.getcwd(), 'al_rased'))
from core.utils.text import normalize_text

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"
MODEL_FILE = "al_rased/features/model/classifier.joblib"
SOURCE_DIRS = [
    "/Users/apple/qxqbotv3/data/telethonSamples",
    "/Users/apple/qxqbotv3/data/telethonSamplesv2"
]

# Enhanced patterns for weak categories
ENHANCED_PATTERNS = {
    "Hacking": [
        # Real hacking services
        re.compile(r"اختراق.*?(حساب|سناب|انستا|واتس|تويتر)", re.I),
        re.compile(r"تهكير.*?(حساب|جوال|هاتف)", re.I),
        re.compile(r"استرجاع.*?حساب.*?(مسروق|مخترق)", re.I),
        re.compile(r"تجسس.*?(واتساب|واتس|رسائل)", re.I),
        re.compile(r"فتح.*?حساب.*?مقفل", re.I),
        re.compile(r"كشف.*?(موقع|مكان).*?شخص", re.I),
        re.compile(r"برنامج.*?تجسس", re.I),
    ],
    "Spam": [
        re.compile(r"(شحن|رشق).*?(متابعين|لايكات|مشاهدات)", re.I),
        re.compile(r"(قسائم|كوبون|كود خصم).*?(نون|امازون|شي ان)", re.I),
        re.compile(r"اشتراك.*?(نتفلكس|شاهد|سبوتيفاي|يوتيوب)", re.I),
        re.compile(r"شحن.*?(شدات|جواهر|الماس)", re.I),
        re.compile(r"متجر.*?الكتروني.*?(سلة|زد)", re.I),
        re.compile(r"خدمات.*?(تصميم|برمجة|تسويق)", re.I),
    ],
    "Financial Scams": [
        re.compile(r"(قرض|تمويل).*?(بدون|فوري|سريع)", re.I),
        re.compile(r"تصفير.*?(مديونية|سمة)", re.I),
        re.compile(r"(راتب|وظيفة).*?بدون.*?عمل", re.I),
        re.compile(r"ربح.*?(يومي|مضمون|استثمار)", re.I),
        re.compile(r"تداول.*?(عملات|فوركس|كريبتو)", re.I),
        re.compile(r"سعوده.*?وهميه", re.I),
    ],
    "Academic Cheating": [
        re.compile(r"حل.*?(واجبات|اختبارات|كويزات)", re.I),
        re.compile(r"(بحوث|مشاريع).*?تخرج", re.I),
        re.compile(r"cv.*?احترافي", re.I),
        re.compile(r"عرض.*?بوربوينت", re.I),
    ]
}

# Safe patterns (should be Normal)
SAFE_PATTERNS = [
    re.compile(r"(كيف|وش|شنو|ايش).*?\?", re.I),
    re.compile(r"(احد|مين).*?(يعرف|جرب)", re.I),
    re.compile(r"السلام عليكم.*?\?", re.I),
]

def load_all_messages():
    import glob
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
                        if txt and 20 < len(txt) < 800 and txt not in seen:
                            messages.append(txt)
                            seen.add(txt)
            except: pass
    return messages

def enhanced_mining():
    """Mine for samples matching enhanced patterns."""
    import joblib
    
    print("Loading model and messages...")
    clf = joblib.load(MODEL_FILE)
    messages = load_all_messages()
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    existing_texts = {d['text'] for d in training_data}
    
    print(f"Scanning {len(messages)} messages with enhanced patterns...")
    
    new_samples = []
    for text in messages:
        if text in existing_texts:
            continue
            
        norm_text = normalize_text(text)
        
        # Check if safe (skip)
        if any(p.search(text) for p in SAFE_PATTERNS):
            continue
        
        # Check enhanced patterns
        for cat, patterns in ENHANCED_PATTERNS.items():
            if any(p.search(text) or p.search(norm_text) for p in patterns):
                new_samples.append({
                    "text": text,
                    "label": cat,
                    "reviewed_by": "enhanced_miner",
                    "note": f"Matched enhanced pattern for {cat}"
                })
                existing_texts.add(text)
                break
    
    print(f"Found {len(new_samples)} new samples from enhanced patterns.")
    
    # Limit per category
    from collections import Counter
    by_cat = {}
    for s in new_samples:
        cat = s['label']
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(s)
    
    final_samples = []
    for cat, samples in by_cat.items():
        random.shuffle(samples)
        final_samples.extend(samples[:100])  # Max 100 per category
        print(f"  {cat}: {min(len(samples), 100)} added")
    
    if final_samples:
        training_data.extend(final_samples)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
    
    return len(final_samples)

def run_training():
    """Run model training."""
    print("\n=== Training Model ===")
    subprocess.run([sys.executable, "-u", "al_rased/features/model/train.py"], 
                   cwd="/Users/apple/qxqbotv3")

def run_calibration():
    """Run threshold calibration."""
    print("\n=== Calibrating Thresholds ===")
    subprocess.run([sys.executable, "scripts/calibrate_thresholds.py"], 
                   cwd="/Users/apple/qxqbotv3")

def run_simulation():
    """Run simulation and return summary."""
    print("\n=== Running Simulation ===")
    result = subprocess.run(
        [sys.executable, "scripts/simulate_with_score.py"],
        cwd="/Users/apple/qxqbotv3",
        capture_output=True,
        text=True
    )
    return result.stdout

def main():
    MAX_ITERATIONS = 5
    
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n{'='*60}")
        print(f"=== ITERATION {iteration}/{MAX_ITERATIONS} ===")
        print(f"{'='*60}")
        
        # 1. Enhanced Mining
        added = enhanced_mining()
        
        if added == 0 and iteration > 1:
            print("No new samples found. Convergence reached.")
            break
        
        # 2. Training
        run_training()
        
        # 3. Calibration
        run_calibration()
        
        # 4. Simulation
        output = run_simulation()
        
        # Extract key metrics
        lines = output.split('\n')
        for line in lines:
            if 'Total Violations Detected' in line or 'Potential Misses' in line:
                print(f"  >> {line.strip()}")
    
    print(f"\n{'='*60}")
    print("=== OPTIMIZATION COMPLETE ===")
    print(f"{'='*60}")
    
    # Final full simulation output
    subprocess.run([sys.executable, "scripts/simulate_with_score.py"], 
                   cwd="/Users/apple/qxqbotv3")

if __name__ == "__main__":
    main()
