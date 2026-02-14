import json
import os
import re
import random
import glob

# Configuration
SOURCE_DIR = "/Users/apple/qxqbotv3/data/telethonSamples"
LABELED_FILE = "/Users/apple/qxqbotv3/al_rased/data/labeledSamples/training_data.json"
NEW_SAMPLES_LIMIT = 50

# Regex for "Hard" Normal (Innocent questions containing risky words)
HARD_NORMAL_PATTERNS = [
    # Medical context: asking about procedure, not buying
    re.compile(r"(كيف|طريقة|شلون|متى|وين).*(ارفع|اجيب|اطلع).*(عذر|تقرير|سكليف|اجازة)", re.IGNORECASE),
    re.compile(r"(عذر|تقرير|سكليف).*(مقبول|نظام|الجامعة|الكلية|التراكمي|الغياب)", re.IGNORECASE),
    # Hacking context: asking for help/recovery, not services
    re.compile(r"(نسيت|ضاع|انسحب|انسرق).*(حساب|رقم|باسورد|كلمة السر)", re.IGNORECASE),
    re.compile(r"(كيف|طريقة).*(استرجع|ارجع).*(حساب|ايميل)", re.IGNORECASE),
    # General innocent
    re.compile(r"(عندي|تواجهني).*(مشكلة).*(تسجيل|دخول|الموقع)", re.IGNORECASE),
]

# Regex for "Financial Scams" (Broader to catch more)
FINANCIAL_PATTERNS = [
    re.compile(r"(قرض|تمويل|سلفة|دعم).{0,20}(فوري|بدون|سداد|ميسر|بدون كفيل|للمتعثرين)", re.IGNORECASE),
    re.compile(r"(استخراج|تصفير|تنزيل).{0,20}(قروض|مديونية|سمة|صندوق)", re.IGNORECASE),
    re.compile(r"(راتب).{0,15}(بدون عمل|بدون دوام)", re.IGNORECASE),
     re.compile(r"(تصفير).{0,15}(الضريبة|الزكاة)", re.IGNORECASE),
]

# Regex for "Hacking" (Specific services)
HACKING_PATTERNS = [
    re.compile(r"(بيع|توفير).{0,15}(ثغرات|ادوات).{0,10}(اختراق|هكر)", re.IGNORECASE),
    re.compile(r"(فتح|فك).{0,15}(كام|جوال|ايكلاود).{0,10}(عن بعد)", re.IGNORECASE),
    re.compile(r"(تجسس|مراقبة).{0,15}(واتس|سناب|مكالمات)", re.IGNORECASE),
]

def load_data():
    files = glob.glob(os.path.join(SOURCE_DIR, "*.json"))
    messages = []
    print(f"Scanning {len(files)} files...")
    for fpath in files:
        if "_metadata.json" in fpath: continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                msgs = data if isinstance(data, list) else data.get('messages', [])
                for m in msgs:
                    txt = m.get('message') or m.get('text')
                    if txt: messages.append(txt)
        except: pass
    return messages

def is_sales_spam(text):
    # Filter out obvious sales to avoid confusing Hard Normal
    return re.search(r"(تواصل|واتس|خاص|سعر|مقابل|انجاز|مضمون|للتواصل)", text)

def main():
    messages = load_data()
    print(f"Total messages: {len(messages)}")
    
    new_samples = []
    seen_texts = set()
    
    # Load existing to avoid duplicates
    if os.path.exists(LABELED_FILE):
        with open(LABELED_FILE, 'r') as f:
            existing = json.load(f)
            for item in existing:
                seen_texts.add(item['text'])

    financial_count = 0
    hard_normal_count = 0
    hacking_count = 0

    for text in messages:
        if text in seen_texts: continue
        if len(text) < 15 or len(text) > 500: continue
        
        # Check Financial
        is_fin = any(p.search(text) for p in FINANCIAL_PATTERNS)
        if is_fin and financial_count < 30:
            new_samples.append({"text": text, "label": "Financial Scams", "dataset": "gap_fix"})
            seen_texts.add(text)
            financial_count += 1
            continue

        # Check Hacking
        is_hack = any(p.search(text) for p in HACKING_PATTERNS)
        if is_hack and hacking_count < 20:
             new_samples.append({"text": text, "label": "Hacking", "dataset": "gap_fix"})
             seen_texts.add(text)
             hacking_count += 1
             continue
             
        # Check Hard Normal
        starts_hard = any(p.search(text) for p in HARD_NORMAL_PATTERNS)
        if starts_hard and not is_sales_spam(text) and hard_normal_count < 30:
            new_samples.append({"text": text, "label": "Normal", "dataset": "gap_fix_hard_negative"})
            seen_texts.add(text)
            hard_normal_count += 1
            continue

    print(f"Found new samples: Financial={financial_count}, Hacking={hacking_count}, HardNormal={hard_normal_count}")
    
    # Append
    if os.path.exists(LABELED_FILE):
        with open(LABELED_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = []
        
    for s in new_samples:
        data.append({
            "text": s['text'],
            "label": s['label'],
            "reviewed_by": "antigravity_refiner",
            "review_status": "auto_added"
        })
        
    with open(LABELED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Updated {LABELED_FILE} with {len(new_samples)} new samples.")

if __name__ == "__main__":
    main()
