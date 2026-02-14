#!/usr/bin/env python3
"""
Mine group_messages for Unethical content samples
"""
import json
import os
import glob

print('🔍 Mining Group Messages for Unethical Content')
print('=' * 70)

# Keywords for unethical content (expanded)
unethical_keywords = [
    # Sexual exploitation / Adult content promotion
    'افلام اطفال', 'اغتصاب', 'تحرش', 'قاصر', 'عاري', 'سكس', 'نيك',
    'بورن', 'porn', 'xxx', 'sex', 'nude', 'onlyfans',
    'شيميل', 'سحاق', 'لواط', 'شواذ',
    # Videos promotion
    'فيديوهات ساخنة', 'مقاطع خاصة', 'محتوى للكبار', 'فقط للكبار',
    '+18', '18+', 'للكبار فقط',
    # Violence
    'ذبح', 'تعذيب', 'قتل مباشر',
    # Drugs
    'حشيش', 'مخدرات', 'كوكايين', 'هيروين', 'شبو', 'كريستال',
    'حبوب منومة', 'ترامادول', 'كبتاجون',
    # Weapons
    'اسلحة للبيع', 'مسدس للبيع', 'رشاش', 'متفجرات',
    # Human trafficking
    'رقيق', 'اتجار بالبشر', 'عبودية', 'بنات للبيع',
    # Surveillance / Spying
    'تجسس على', 'مراقبة زوج', 'كاميرات مراقبه', 'تصوير خفي',
]

mined_samples = []

# Search in group_messages
group_messages_path = 'al_rased/data/group_messages'

if os.path.exists(group_messages_path):
    json_files = glob.glob(f'{group_messages_path}/*.json')
    print(f'Found {len(json_files)} group message files')
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                messages = json.load(f)
            
            for msg in messages:
                txt = msg.get('text', '').lower() if isinstance(msg, dict) else ''
                full_text = msg.get('text', '') if isinstance(msg, dict) else ''
                
                # Check for unethical keywords
                if any(k in txt for k in unethical_keywords):
                    if len(full_text) > 30:  # Skip very short
                        mined_samples.append({
                            'text': full_text,
                            'label': 'Unethical',
                            'source': 'group_messages',
                            'matched_keyword': next((k for k in unethical_keywords if k in txt), '')
                        })
        except Exception as e:
            continue

# Deduplicate
unique_mined = list({s['text']: s for s in mined_samples}.values())
print(f'\n📊 Results:')
print(f'   Total matches: {len(mined_samples)}')
print(f'   Unique samples: {len(unique_mined)}')

# Show samples
print(f'\n📋 Sample Preview (first 15):')
for i, s in enumerate(unique_mined[:15], 1):
    txt = s['text'].replace('\n', ' ')[:100]
    kw = s.get('matched_keyword', '')
    print(f'{i}. [{kw}] {txt}...')

# Save to training data
if unique_mined:
    file_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Add unique samples (max 100)
    added = 0
    existing_texts = {d['text'] for d in data}
    for s in unique_mined[:100]:
        if s['text'] not in existing_texts:
            data.append({
                'text': s['text'],
                'label': 'Unethical',
                'source': 'mined_group_messages'
            })
            added += 1
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f'\n✅ Added {added} new Unethical samples to training data')
