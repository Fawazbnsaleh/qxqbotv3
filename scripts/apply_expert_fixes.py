
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Expert Rules (Regex Patterns) - Expanded with typos and obfuscations
EXPERT_RULES = {
    'Academic Cheating': [
        r'حل\s*واجب', r'حل\s*اختبار', r'مشاريع\s*تخرج', r'رسائ?ل\s*ماجستير', 
        r'اعداد\s*بحوث', r'خدمات\s*طلابية', r'اسايمنت', r'كويزات', r'تسميع',
        r'حلول\s*واجبات', r'مساعدة\s*في\s*الاختبار', r'قروب\s*حل', r'أبحاث\s*جامعية',
        r'امتحانت', r'اساينمنت', r'بروجكت', r'تلقرام', r'قروبات\s*جامعية'
    ],
    'Medical Fraud': [
        r'سكليف', r'اجازة\s*مرضية', r'تقرير\s*طبي', r'عذر\s*طبي', r'مشهد\s*مرافقة',
        r'مستشفى\s*حكومي', r'منصة\s*صحتي', r'تطبيق\s*صحتي', r'مرضيه\s*معتمده',
        r'اجازه\s*مرضيه', r'سك\s*ليف'
    ],
    'Financial Scams': [
        r'استثم[رار]', r'ارباح\s*مضمونة', r'تداول', r'فوركس', r'عملات\s*رقمية',
        r'ادارة\s*محافظ', r'ربح\s*يومي', r'دخل\s*اضافي', r'توصيات\s*ذهب',
        r'crypto', r'bitcoin', r'usdt', r'binance', r'investment', r'profit',
        r'بيتكوين', r'ايثيريوم', r'عملات', r'اسهم'
    ],
    'Hacking': [
        r'تهكير', r'اختراق', r'تجسس', r'سحب\s*صور', r'استرداد\s*حساب',
        r'زيادة\s*متابعين', r'توثيق\s*حساب', r'رشق', r'متابعين',
        r'ارقام\s*وهمية' # Moved from Spam
    ],
    'Unethical': [
        r'سكس', r'ني[كڪ]', r'ممحون', r'ديوث', r'قحبة', r'سهرات', r'مساج', r'مدلعة',
        r'حشيش', r'مخدرات', r'كبتاجون', r'شبو', r'نودز', r'افلام\s*اباحية', r'زنا'
    ],
    # Spam is usually a fallback if others don't match but contains generic ad keywords
    'Spam': [
        r'سيرفر\s*ماينكرافت', r'تبادل\s*نشر', r'اشترك\s*في\s*قناتنا', 
        r'تفعيل\s*تليجرام'
    ]
}

def clean_text(text):
    return text.lower()

def check_expert_rules(text):
    text = clean_text(text)
    matches = []
    for label, patterns in EXPERT_RULES.items():
        for pattern in patterns:
            if re.search(pattern, text):
                matches.append((label, pattern))
    return matches

def main():
    print("🤖 Starting Expert Data Quality Audit...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)
    print(f"📊 Analyzing {len(data)} samples...")

    corrected_count = 0
    verified_count = 0
    
    for sample in data:
        text = sample['text']
        original_label = sample.get('label', 'Normal')
        original_labels = sample.get('labels', [original_label])
        if isinstance(original_labels, str): original_labels = [original_labels]

        expert_matches = check_expert_rules(text)
        expert_labels = list(set([m[0] for m in expert_matches]))

        # 1. Correction Logic
        if expert_labels:
            # Check if any new labels need to be added
            new_labels = set(original_labels)
            labels_changed = False
            
            for expert_label in expert_labels:
                if expert_label not in new_labels:
                    # Strict Logic:
                    # - If Normal/Spam -> Violation: FORCE ADD
                    # - If Violation -> Different Violation: FORCE ADD (Multi-label)
                    
                    if 'Normal' in new_labels:
                        new_labels.remove('Normal') # Remove Normal if adding violation
                        labels_changed = True
                    if 'Spam' in new_labels and expert_label != 'Spam':
                        # Valid discussion: Keep Spam if it's spammy, but usually violation supersedes
                        # For now, let's keep Spam if meaningful, but usually not
                        if len(new_labels) == 1: # If only Spam
                             new_labels.remove('Spam')
                        labels_changed = True
                    
                    new_labels.add(expert_label)
                    labels_changed = True

            if labels_changed:
                sample['labels'] = list(new_labels)
                sample['label'] = sample['labels'][0] # Backward compat
                match_patterns = [m[1] for m in expert_matches]
                sample['note'] = f"Corrected by Gemini: Detected keywords {match_patterns}"
                sample['corrected_at'] = datetime.now().isoformat()
                corrected_count += 1
            else:
                 # Already has the labels, just verify
                 match_patterns = [m[1] for m in expert_matches]
                 if 'Verified' not in sample.get('note', ''):
                    sample['note'] = f"Verified: Contains {match_patterns}"
                    verified_count += 1
        
        # 2. Financial Scam Specific Check (ETH, Crypto) in Normal
        # Already covered by regex but double check English terms if needed
        if 'Normal' in original_labels:
            if re.search(r'\b(eth|btc|usdt|profit|invest)\b', text, re.I):
                sample['label'] = 'Financial Scams'
                sample['labels'] = ['Financial Scams']
                sample['note'] = "Corrected by Gemini: Detected English crypto terms"
                sample['corrected_at'] = datetime.now().isoformat()
                corrected_count += 1

    # Save
    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Audit Complete.")
    print(f"🔧 Corrected: {corrected_count} samples")
    print(f"✅ Verified: {verified_count} samples")

if __name__ == "__main__":
    main()
