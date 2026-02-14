"""
Manual Labeling Script.
Extracts confirmed violations from simulation misses and adds them to training data.
"""
import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'al_rased'))

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"
SIMULATION_FILE = "al_rased/data/results/simulation_v2_scored.json"

# Patterns that are DEFINITELY violations when seen
DEFINITE_VIOLATION_KEYWORDS = {
    "Medical Fraud": [
        "اجازة مرضية جاهزة",
        "سكليف رسمي",
        "عذر طبي معتمد",
        "اعذار طبية معتمد",
        "كروت تطعيم",
        "تقارير طبية للبيع",
        "نطلع سكليف",
        "يطلع سكليف",
        "تسوي سكليف",
        "عندها اعذار",
        "إعتمدها",
    ],
    "Academic Cheating": [
        "حل واجبات واختبارات",
        "ابحاث عروض بوربوينت",
        "مشاريع تخرج",
        "cv احترافي حل واجبات",
    ],
    "Financial Scams": [
        "راتب بدون عمل",
        "ربح يومي",
        "استثمار مضمون",
    ],
    "Spam": [
        "متجر الكتروني على سلة",
        "شحن شدات",
    ]
}

def run_manual_labeling():
    # Load simulation results
    with open(SIMULATION_FILE, 'r', encoding='utf-8') as f:
        sim_data = json.load(f)
    
    # Load training data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    
    existing_texts = {d['text'] for d in training_data}
    
    # Find misses that match definite patterns
    new_samples = []
    
    for item in sim_data:
        if item.get('missed_oracle_category'):
            text = item['text']
            text_lower = text.lower()
            
            # Check if matches definite patterns
            for cat, keywords in DEFINITE_VIOLATION_KEYWORDS.items():
                for kw in keywords:
                    if kw in text_lower or kw in text:
                        if text not in existing_texts:
                            new_samples.append({
                                "text": text,
                                "label": cat,
                                "reviewed_by": "manual_review",
                                "note": f"Matched definite pattern: {kw}"
                            })
                            existing_texts.add(text)
                        break
    
    print(f"Found {len(new_samples)} confirmed violations from misses.")
    
    if new_samples:
        # Add to training data
        training_data.extend(new_samples)
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        # Show what was added
        from collections import Counter
        counts = Counter(s['label'] for s in new_samples)
        print("Added by category:")
        for cat, cnt in counts.items():
            print(f"  {cat}: {cnt}")
    
    print("Training data updated.")

if __name__ == "__main__":
    run_manual_labeling()
