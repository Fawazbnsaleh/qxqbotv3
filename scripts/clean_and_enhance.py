"""
Clean Duplicates and Find Unique Samples.
1. Remove duplicate samples from training data
2. Mine Telethon for new unique samples for weak categories
"""
import json
import os
import sys
import glob
import re
import random

sys.path.append(os.path.join(os.getcwd(), 'al_rased'))
from core.utils.text import normalize_text

DATA_FILE = "al_rased/data/labeledSamples/training_data.json"
SOURCE_DIRS = [
    "/Users/apple/qxqbotv3/data/telethonSamples",
    "/Users/apple/qxqbotv3/data/telethonSamplesv2"
]

# Expanded patterns for weak categories
PATTERNS = {
    "Hacking": [
        re.compile(r"اختراق|تهكير|تجسس|سرقة.*حساب", re.I),
        re.compile(r"فتح.*حساب.*مقفل|فك.*رمز|كسر.*باسورد", re.I),
        re.compile(r"مراقبة.*(هاتف|جوال|واتس)", re.I),
        re.compile(r"برنامج.*تجسس|تطبيق.*تجسس", re.I),
        re.compile(r"استرجاع.*حساب.*(مسروق|مهكر)", re.I),
    ],
    "Spam": [
        re.compile(r"(شحن|رشق).*(متابعين|لايكات|مشاهدات|نجوم)", re.I),
        re.compile(r"(قسائم|كوبون|كود خصم).*(نون|امازون|شي ان)", re.I),
        re.compile(r"اشتراك.*(نتفلكس|شاهد|سبوتيفاي|ستارز)", re.I),
        re.compile(r"شحن.*(شدات|جواهر|الماس|يوسي)", re.I),
        re.compile(r"متجر.*الكتروني.*(سلة|زد)", re.I),
        re.compile(r"خدمات.*(تصميم|برمجة|تسويق)", re.I),
        re.compile(r"زيادة.*(متابعين|لايكات)", re.I),
    ],
    "Financial Scams": [
        re.compile(r"(قرض|تمويل|سلفة).*(بدون كفيل|فوري|سريع)", re.I),
        re.compile(r"تصفير.*(مديونية|سمة|قروض)", re.I),
        re.compile(r"(راتب|وظيفة).*بدون.*عمل", re.I),
        re.compile(r"ربح.*(يومي|مضمون|استثمار)", re.I),
        re.compile(r"تداول.*(عملات|فوركس|كريبتو)", re.I),
        re.compile(r"سعوده.*(وهمي|بدون عمل)", re.I),
        re.compile(r"استثمار.*مضمون", re.I),
    ]
}

# Exclude patterns (innocent messages)
EXCLUDE = [
    re.compile(r"كيف|ايش|وش|شنو.*\?", re.I),
    re.compile(r"احد.*يعرف|مين.*جرب", re.I),
]

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
                        if txt and 30 < len(txt) < 800 and txt not in seen:
                            messages.append(txt)
                            seen.add(txt)
            except: pass
    return messages

def clean_and_enhance():
    print("=" * 60)
    print("PHASE 1: REMOVING DUPLICATES")
    print("=" * 60)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Remove duplicates, keep first occurrence
    seen_texts = set()
    unique_data = []
    removed = 0
    
    for d in data:
        if d['text'] not in seen_texts:
            unique_data.append(d)
            seen_texts.add(d['text'])
        else:
            removed += 1
    
    print(f"Removed {removed} duplicate samples.")
    print(f"Remaining: {len(unique_data)} unique samples.")
    
    # Count by category
    by_label = {}
    for d in unique_data:
        by_label[d['label']] = by_label.get(d['label'], 0) + 1
    
    print("\nUnique counts per category:")
    for label, count in sorted(by_label.items()):
        print(f"  {label}: {count}")
    
    print("\n" + "=" * 60)
    print("PHASE 2: MINING NEW UNIQUE SAMPLES")
    print("=" * 60)
    
    messages = load_all_messages()
    print(f"Scanning {len(messages)} messages...")
    
    new_samples = {cat: [] for cat in PATTERNS}
    
    for text in messages:
        if text in seen_texts:
            continue
        
        # Skip if matches exclude patterns
        if any(p.search(text) for p in EXCLUDE):
            continue
        
        norm = normalize_text(text)
        
        for cat, patterns in PATTERNS.items():
            if any(p.search(text) or p.search(norm) for p in patterns):
                new_samples[cat].append({
                    "text": text,
                    "label": cat,
                    "reviewed_by": "diversity_miner",
                    "note": "New unique sample"
                })
                seen_texts.add(text)
                break
    
    # Add samples to reach target
    TARGET_PER_CAT = 300  # Target unique samples per category
    
    for cat, samples in new_samples.items():
        current = by_label.get(cat, 0)
        needed = max(0, TARGET_PER_CAT - current)
        
        random.shuffle(samples)
        to_add = samples[:needed]
        unique_data.extend(to_add)
        
        print(f"{cat}: Found {len(samples)}, Added {len(to_add)} (had {current}, target {TARGET_PER_CAT})")
    
    # Save
    random.shuffle(unique_data)
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nFinal dataset: {len(unique_data)} samples")
    
    # Final counts
    final_counts = {}
    for d in unique_data:
        final_counts[d['label']] = final_counts.get(d['label'], 0) + 1
    
    print("\nFinal distribution:")
    for label, count in sorted(final_counts.items()):
        print(f"  {label}: {count}")

if __name__ == "__main__":
    clean_and_enhance()
