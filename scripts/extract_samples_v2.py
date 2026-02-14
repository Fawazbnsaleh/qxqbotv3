import json
import os
import re
import random
import glob

# Configuration
SOURCE_DIR = "/Users/apple/qxqbotv3/data/telethonSamples"
OUTPUT_FILE = "/Users/apple/qxqbotv3/al_rased/data/samples4Review/data.json"
SAMPLES_PER_CATEGORY = 50

# Regex Patterns for Categories
PATTERNS = {
    "Academic Cheating": [
        r"حل\s+(واجبات|كويزات|اختبارات|اسايمنت)",
        r"بحوث\s+(جامعية|تخرج|علمية)",
        r"مشاريع\s+تخرج",
        r"رسائل\s+(ماجستير|دكتوراه)",
        r"تحليل\s+احصائي",
        r"اعداد\s+بحوث"
    ],
    "Medical Fraud": [
        r"سكليف",
        r"اجازة\s+مرضية",
        r"عذر\s+طبي",
        r"تقرير\s+طبي",
        r"صحتي",
        r"شهادة\s+صحية"
    ],
    "Financial Scams": [
        r"قرض\s+(شخصي|عقاري)",
        r"تسديد\s+قروض",
        r"رفع\s+سكور",
        r"راتب\s+بدون\s+عمل",
        r"استخراج\s+قرض",
        r"تمويل\s+بدون"
    ],
    "Hacking": [
        r"هكر",
        r"اختراق",
        r"تجسس",
        r"استرجاع\s+حسابات",
        r"تطيير\s+حسابات",
        r"فك\s+حظر",
        r"تعليم\s+هكر"
    ],
    "Spam": [
        r"سيرفر\s+ماين\s+كرافت",
        r"رشق\s+متابعين",
        r"اشتراك\s+(نتفليكس|شاهد|iptv)",
        r"زيادة\s+متابعين",
        r"متجر\s+الكتروني",
        r"عروض\s+حصرية"
    ]
}

# Compile Regex
COMPILED_PATTERNS = {
    cat: [re.compile(p, re.IGNORECASE) for p in patterns]
    for cat, patterns in PATTERNS.items()
}

def load_messages():
    files = glob.glob(os.path.join(SOURCE_DIR, "*.json"))
    all_messages = []
    print(f"Loading from {len(files)} files...")
    
    for fpath in files:
        if "_metadata.json" in fpath:
            continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both list of messages or dict with 'messages' key
                if isinstance(data, list):
                    msgs = data
                elif isinstance(data, dict) and 'messages' in data:
                    msgs = data['messages']
                else:
                    continue
                
                for m in msgs:
                    if isinstance(m, dict) and 'message' in m and m['message']:
                        all_messages.append(m['message']) # Telethon JSON usually has 'message' key for text
                    elif isinstance(m, dict) and 'text' in m and m['text']:
                        all_messages.append(m['text']) # Some formats might use 'text'

        except Exception as e:
            print(f"Error reading {fpath}: {e}")
            
    print(f"Total messages loaded: {len(all_messages)}")
    return all_messages

def classify_message(text):
    for category, regexes in COMPILED_PATTERNS.items():
        for regex in regexes:
            if regex.search(text):
                return category
    return "Normal"

def main():
    messages = load_messages()
    
    categorized_samples = {cat: [] for cat in PATTERNS.keys()}
    categorized_samples["Normal"] = []
    
    seen_texts = set()
    
    for text in messages:
        # Cleanup
        text = text.strip()
        if len(text) < 10 or len(text) > 1000: # Filter too short/long
            continue
            
        if text in seen_texts:
            continue
        
        category = classify_message(text)
        
        # Heuristic for Normal: simple check to ensure it doesnt contain suspicious words not caught by list
        if category == "Normal":
            # Extra safety for 'Normal': Must not have phone numbers or links generally (optional, but good for pure normal samples)
            # For now, just accept it if it didn't match any violation patterns.
            pass
            
        if len(categorized_samples[category]) < SAMPLES_PER_CATEGORY:
            categorized_samples[category].append({
                "text": text,
                "category": category
            })
            seen_texts.add(text)
            
    # Combine
    final_results = []
    stats = {}
    for cat, samples in categorized_samples.items():
        final_results.extend(samples)
        stats[cat] = len(samples)
        
    # Shuffle
    random.shuffle(final_results)
    
    output_data = {
        "categories": list(PATTERNS.keys()) + ["Normal"],
        "samples": final_results
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print("Extraction Complete.")
    print("Statistics:")
    for cat, count in stats.items():
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    main()
