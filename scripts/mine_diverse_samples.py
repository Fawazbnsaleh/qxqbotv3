#!/usr/bin/env python3
"""
Mine MORE DIVERSE samples for Unethical and Hacking categories
Focus on different patterns and phrasings to improve model recall
"""
import json
import os
import glob
import random

print('🔍 Mining Diverse Samples for Weak Categories')
print('=' * 70)

# ========== EXPANDED KEYWORD PATTERNS ==========

# Unethical - Multiple phrasings of same concepts
unethical_patterns = [
    # Sexual content - various phrasings
    'سكس', 'نيك', 'بورن', 'porn', 'xxx', 'افلام للكبار', 'محتوى للكبار', '+18',
    '18+', 'فيديوهات ساخنة', 'مقاطع خاصة', 'بدون ملابس', 'عاري', 'nude',
    'onlyfans', 'فقط للكبار', 'هيجانه', 'نودز', 'فيديو كول', 'سكس شات',
    # Child exploitation
    'اطفال', 'قاصر', 'صغير', 'تحرش',
    # LGBT content (may be considered unethical in some contexts)
    'شيميل', 'سحاق', 'لواط', 'شواذ', 'مثلي',
    # Violence
    'ذبح', 'تعذيب', 'قتل', 'دم', 'جثث',
    # Drugs - expanded
    'حشيش', 'مخدرات', 'كوكايين', 'هيروين', 'شبو', 'كريستال', 'كبتاجون',
    'ترامادول', 'حبوب', 'منشطات', 'مهلوسات',
    # Weapons
    'اسلحة', 'مسدس', 'رشاش', 'بندقية', 'سلاح', 'ذخيرة',
    # Spy/Surveillance services
    'تجسس', 'مراقبة', 'تصوير خفي', 'كاميرات سرية',
    # Telegram bot links for adult content
    't.me/', 'bot?start=',
]

# Hacking - Various service patterns
hacking_patterns = [
    # Hacking services
    'تهكير', 'هكر', 'اختراق', 'سرقة حساب', 'فك حماية', 'تجاوز',
    # Account manipulation
    'حظر حساب', 'فتح حساب محظور', 'استرجاع حساب', 'سحب معلومات',
    # Platform-specific hacking
    'تهكير واتساب', 'تهكير انستقرام', 'تهكير تيك توك', 'تهكير سناب',
    'تهكير فيسبوك', 'تهكير تويتر', 'تهكير تلجرام',
    # Phone hacking
    'تهكير جوال', 'تهكير هاتف', 'اختراق هاتف', 'فرمتة عن بعد',
    # Cyber security services (malicious)
    'امن سيبراني', 'فريق هكرز', 'خدمات الهكر',
    # Tools
    'لودر', 'غش', 'شيت', 'cheat', 'hack',
    # Fake followers/likes (borderline)
    'رشق متابعين', 'صيد حسابات', 'يوزرات',
]

# ========== MINING ==========

group_messages_path = 'al_rased/data/group_messages'
mined_unethical = []
mined_hacking = []

if os.path.exists(group_messages_path):
    json_files = glob.glob(f'{group_messages_path}/*.json')
    print(f'Scanning {len(json_files)} group message files...')
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                messages = json.load(f)
            
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                    
                txt = msg.get('text', '').lower()
                full_text = msg.get('text', '')
                
                if len(full_text) < 30:
                    continue
                
                # Check Unethical
                matched_unethical = [k for k in unethical_patterns if k in txt]
                if matched_unethical:
                    # Stronger signal: multiple keywords or explicit content
                    if len(matched_unethical) >= 2 or any(k in txt for k in ['سكس', 'porn', 'xxx', 'نيك', 'هيجانه']):
                        mined_unethical.append({
                            'text': full_text,
                            'label': 'Unethical',
                            'matched': matched_unethical[:3]
                        })
                
                # Check Hacking
                matched_hacking = [k for k in hacking_patterns if k in txt]
                if matched_hacking:
                    # Must have hacking intent, not just asking
                    is_question = any(q in txt for q in ['كيف', 'مين يعرف', 'ابي', 'احتاج'])
                    is_service = any(s in txt for s in ['متوفر', 'للتواصل', 'يوجد لدينا', 'خاص', 'dm'])
                    
                    if is_service and not is_question:
                        mined_hacking.append({
                            'text': full_text,
                            'label': 'Hacking',
                            'matched': matched_hacking[:3]
                        })
        except:
            continue

# Deduplicate
unique_unethical = list({s['text']: s for s in mined_unethical}.values())
unique_hacking = list({s['text']: s for s in mined_hacking}.values())

print(f'\n📊 Mining Results:')
print(f'   Unethical: {len(unique_unethical)} unique samples')
print(f'   Hacking: {len(unique_hacking)} unique samples')

# Load current data
file_path = 'al_rased/data/labeledSamples/training_data.json'
with open(file_path, 'r') as f:
    data = json.load(f)

existing_texts = {d['text'] for d in data}

# Add new unique samples
added_unethical = 0
added_hacking = 0

for s in unique_unethical[:100]:
    if s['text'] not in existing_texts:
        data.append({
            'text': s['text'],
            'label': 'Unethical',
            'source': 'diverse_mining'
        })
        existing_texts.add(s['text'])
        added_unethical += 1

for s in unique_hacking[:100]:
    if s['text'] not in existing_texts:
        data.append({
            'text': s['text'],
            'label': 'Hacking',
            'source': 'diverse_mining'
        })
        existing_texts.add(s['text'])
        added_hacking += 1

with open(file_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'\n✅ Added to training data:')
print(f'   Unethical: +{added_unethical} new samples')
print(f'   Hacking: +{added_hacking} new samples')

# Show new distribution
from collections import Counter
labels = Counter(d['label'] for d in data)
print(f'\n📈 Updated Distribution:')
for lbl, cnt in labels.most_common():
    print(f'   {lbl}: {cnt}')
