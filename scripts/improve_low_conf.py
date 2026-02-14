"""
Improve Low Confidence Detections.
Takes confirmed low-confidence violations and adds them to training data.
"""
import json
import os
import sys
import re
import random

sys.path.append(os.path.join(os.getcwd(), 'al_rased'))

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"
RESULTS_FILE = "al_rased/data/results/simulation_v2_scored.json"

# Confirmation patterns - if text matches these, it's definitely a violation
CONFIRM_PATTERNS = {
    "Medical Fraud": [
        re.compile(r"(سكليف|سڪليف|اجازة مرضية|عذر طبي)", re.I),
        re.compile(r"(صحتي|معتمد|رسمي).*?(عذر|سكليف)", re.I),
        re.compile(r"(نطلع|اطلع|تسوي).*?(اعذار|سكليف)", re.I),
    ],
    "Academic Cheating": [
        re.compile(r"(حل|اسوي|نسوي).*?(واجب|اختبار|كويز|مشروع)", re.I),
        re.compile(r"(بحوث|مشاريع|تقارير).*?(تخرج|جامع)", re.I),
    ],
    "Spam": [
        re.compile(r"(شحن|رشق).*?(متابعين|لايكات|شدات)", re.I),
        re.compile(r"(اشتراك|قسائم|كوبون)", re.I),
    ],
    "Financial Scams": [
        re.compile(r"(ربح|استثمار).*?(يومي|مضمون)", re.I),
        re.compile(r"(راتب|وظيفة).*?بدون.*?عمل", re.I),
    ]
}

def improve_low_confidence():
    print("=" * 60)
    print("IMPROVING LOW CONFIDENCE DETECTIONS")
    print("=" * 60)
    
    # Load current training data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    
    existing_texts = {d['text'] for d in training_data}
    
    # Load simulation results
    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Find low confidence violations (30-50%) that match confirmation patterns
    new_samples = []
    
    for r in results:
        if r['prediction'] == 'Normal':
            continue
        
        confidence = r['confidence']
        label = r['prediction']
        text = r['text']
        
        # Only process low confidence (< 50%)
        if confidence >= 0.50:
            continue
        
        if text in existing_texts:
            continue
        
        # Check if matches confirmation pattern
        patterns = CONFIRM_PATTERNS.get(label, [])
        if any(p.search(text) for p in patterns):
            new_samples.append({
                "text": text,
                "label": label,
                "reviewed_by": "low_conf_improver",
                "note": f"Confirmed low-conf ({confidence:.1%})"
            })
            existing_texts.add(text)
    
    print(f"Found {len(new_samples)} confirmed low-confidence samples.")
    
    # Add to training data
    if new_samples:
        # Limit to avoid overwhelming
        random.shuffle(new_samples)
        to_add = new_samples[:150]  # Max 150 new samples
        training_data.extend(to_add)
        
        # Count by category
        from collections import Counter
        counts = Counter(s['label'] for s in to_add)
        print("Added by category:")
        for cat, cnt in counts.items():
            print(f"  {cat}: {cnt}")
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nTotal training samples: {len(training_data)}")
    else:
        print("No new samples to add.")

if __name__ == "__main__":
    improve_low_confidence()
