"""
Hacking Enhancement + Low Confidence Review Script.
1. Adds real hacking samples (not gaming context)
2. Reviews and confirms low confidence violations
"""
import sys
import os
import json
import glob
import re
import random

sys.path.append(os.path.join(os.getcwd(), 'al_rased'))
from core.utils.text import normalize_text
from features.detection.engine import DetectionEngine

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"
SOURCE_DIRS = [
    "/Users/apple/qxqbotv3/data/telethonSamples",
    "/Users/apple/qxqbotv3/data/telethonSamplesv2"
]

# REAL hacking patterns (criminal activity, not games)
REAL_HACKING_PATTERNS = [
    # Account theft/access
    re.compile(r"اختراق.*?(حساب|سناب|انستا|واتس|تويتر|فيس)", re.I),
    re.compile(r"تهكير.*?(حساب|جوال|هاتف|ايميل)", re.I),
    re.compile(r"سرقة.*?(حساب|بيانات|معلومات)", re.I),
    re.compile(r"استرجاع.*?حساب.*?(مسروق|مخترق|مهكر)", re.I),
    
    # Spying/surveillance
    re.compile(r"تجسس.*?(واتساب|واتس|رسائل|محادثات)", re.I),
    re.compile(r"مراقبة.*?(هاتف|جوال|زوج|زوجة)", re.I),
    re.compile(r"برنامج.*?تجسس", re.I),
    re.compile(r"كشف.*?(موقع|مكان).*?شخص", re.I),
    
    # Password/unlock services
    re.compile(r"فتح.*?(حساب|ايفون|اندرويد).*?(مقفل|قفل)", re.I),
    re.compile(r"فك.*?(حماية|رمز|باسورد)", re.I),
    
    # Explicit hacking services
    re.compile(r"خدمات.*?اختراق", re.I),
    re.compile(r"هكر.*?محترف", re.I),
]

# Gaming context patterns (EXCLUDE these)
GAMING_EXCLUDE = [
    re.compile(r"كلاش|clash|ببجي|pubg|فورت|fortnite|ماين|mine|فري فاير", re.I),
    re.compile(r"لعبة|العاب|سيرفر.*?ماين|جيم", re.I),
]

# Low confidence confirmation patterns
CONFIRM_PATTERNS = {
    "Medical Fraud": [
        re.compile(r"(سكليف|اجازة|عذر).*?(صحتي|طبي|مرضي)", re.I),
        re.compile(r"(نطلع|اطلع|يطلع).*?(اعذار|سكليف)", re.I),
    ],
    "Academic Cheating": [
        re.compile(r"(حل|اسوي).*?(واجب|اختبار|كويز|مشروع)", re.I),
    ],
    "Spam": [
        re.compile(r"(شحن|رشق).*?(متابعين|لايكات)", re.I),
        re.compile(r"(قسائم|كوبون)", re.I),
    ],
    "Financial Scams": [
        re.compile(r"(ربح|استثمار).*?(يومي|مضمون)", re.I),
    ]
}

def load_all_messages():
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

def enhance_hacking():
    """Find and add REAL hacking samples."""
    print("=" * 60)
    print("PHASE 1: ENHANCING HACKING CATEGORY")
    print("=" * 60)
    
    messages = load_all_messages()
    print(f"Scanning {len(messages)} messages for real hacking patterns...")
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    existing_texts = {d['text'] for d in training_data}
    
    hacking_samples = []
    
    for text in messages:
        if text in existing_texts:
            continue
        
        # Check for real hacking patterns
        is_real_hacking = any(p.search(text) for p in REAL_HACKING_PATTERNS)
        is_gaming = any(p.search(text) for p in GAMING_EXCLUDE)
        
        if is_real_hacking and not is_gaming:
            hacking_samples.append({
                "text": text,
                "label": "Hacking",
                "reviewed_by": "hacking_enhancer",
                "note": "Real hacking pattern"
            })
            existing_texts.add(text)
    
    print(f"Found {len(hacking_samples)} real hacking samples.")
    
    # Add up to 100 samples
    random.shuffle(hacking_samples)
    samples_to_add = hacking_samples[:100]
    
    if samples_to_add:
        training_data.extend(samples_to_add)
        print(f"Added {len(samples_to_add)} hacking samples.")
        
        # Show some examples
        print("\nSample hacking messages added:")
        for s in samples_to_add[:5]:
            print(f"  - {s['text'][:80]}...")
    
    return training_data, existing_texts

def review_low_confidence(training_data, existing_texts):
    """Review and confirm low confidence detections."""
    print("\n" + "=" * 60)
    print("PHASE 2: REVIEWING LOW CONFIDENCE DETECTIONS")
    print("=" * 60)
    
    messages = load_all_messages()
    
    # Load thresholds
    try:
        with open("al_rased/features/detection/thresholds.json", 'r') as f:
            THRESHOLDS = json.load(f)
    except:
        THRESHOLDS = {"Medical Fraud": 0.42, "Academic Cheating": 0.39, "Financial Scams": 0.37, "Spam": 0.34}
    
    confirmed = []
    
    print("Scanning for low confidence violations to confirm...")
    
    for text in messages:
        if text in existing_texts:
            continue
        
        result = DetectionEngine.predict(text)
        label = result["label"]
        confidence = result["confidence"]
        threshold = THRESHOLDS.get(label, 0.40)
        
        # Find low confidence violations (30-50%)
        if label != "Normal" and 0.30 <= confidence < 0.50:
            # Check if matches confirmation patterns
            patterns = CONFIRM_PATTERNS.get(label, [])
            if any(p.search(text) for p in patterns):
                confirmed.append({
                    "text": text,
                    "label": label,
                    "reviewed_by": "low_conf_reviewer",
                    "note": f"Confirmed low conf ({confidence:.1%})"
                })
                existing_texts.add(text)
    
    print(f"Confirmed {len(confirmed)} low confidence violations.")
    
    # Add up to 200 confirmed samples
    random.shuffle(confirmed)
    samples_to_add = confirmed[:200]
    
    if samples_to_add:
        training_data.extend(samples_to_add)
        print(f"Added {len(samples_to_add)} confirmed samples.")
        
        # Breakdown by category
        from collections import Counter
        counts = Counter(s['label'] for s in samples_to_add)
        print("By category:", dict(counts))
    
    return training_data

def main():
    # Phase 1: Enhance Hacking
    training_data, existing_texts = enhance_hacking()
    
    # Phase 2: Review Low Confidence
    training_data = review_low_confidence(training_data, existing_texts)
    
    # Save updated training data
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"TOTAL TRAINING SAMPLES: {len(training_data)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
