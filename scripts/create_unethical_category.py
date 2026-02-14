#!/usr/bin/env python3
"""
1. Clean up Hacking samples
2. Create new "Unethical" category
3. Mine raw messages for unethical content
"""
import json
import os
import glob

print('🧹 Cleaning Hacking + Creating Unethical Category')
print('=' * 70)

file_path = 'al_rased/data/labeledSamples/training_data.json'
with open(file_path, 'r') as f:
    data = json.load(f)

# ========== 1. Clean Hacking Samples ==========
print('\n📂 1. Cleaning Hacking Samples...')

# Move crypto analysis to Financial/Normal
# Move questions to Normal
# Move illegal content to new "Unethical" category
fixes = {'to_financial': 0, 'to_normal': 0, 'to_unethical': 0}

for d in data:
    if d.get('label') == 'Hacking':
        txt = d.get('text', '').lower()
        
        # Crypto analysis -> Financial or Normal
        if any(k in txt for k in ['حيتان', 'صفقات', 'بيتكوين', 'bitcoin', 'مستثمرين', 'long']):
            d['label'] = 'Normal'  # It's just news/analysis
            d['fixed_by'] = 'hacking_cleanup'
            fixes['to_normal'] += 1
        
        # Questions (not offering services) -> Normal
        elif any(k in txt for k in ['جاني مبلغ', 'احتاج لودر', 'انت تريده']) and 'للتواصل' not in txt:
            d['label'] = 'Normal'
            d['fixed_by'] = 'hacking_cleanup'
            fixes['to_normal'] += 1
        
        # Illegal content (child abuse, sexual content promotion) -> Unethical
        elif any(k in txt for k in ['افلام اطفال', 'اغتصاب', 'تحرش', 'قاصر', 'سحاق', 'شيميل']):
            d['label'] = 'Unethical'
            d['fixed_by'] = 'hacking_cleanup'
            fixes['to_unethical'] += 1

print(f'   Moved to Normal: {fixes["to_normal"]}')
print(f'   Moved to Financial: {fixes["to_financial"]}')
print(f'   Moved to Unethical: {fixes["to_unethical"]}')

# ========== 2. Mine Raw Messages for Unethical Content ==========
print('\n📂 2. Mining Raw Messages for Unethical Content...')

# Keywords for unethical content
unethical_keywords = [
    # Sexual exploitation
    'افلام اطفال', 'اغتصاب', 'تحرش', 'قاصر', 'بدون ملابس', 'عاري', 'سكس',
    'بورن', 'porn', 'xxx', 'sex', 'nude',
    # Violence
    'قتل', 'ذبح', 'تعذيب',
    # Drugs
    'حشيش', 'مخدرات', 'كوكايين', 'هيروين', 'شبو',
    # Weapons
    'اسلحة', 'مسدس', 'رشاش', 'متفجرات',
    # Exploitation
    'رقيق', 'اتجار بالبشر', 'عبودية',
]

# Search in raw messages
raw_messages_path = 'al_rased/data/raw_messages'
mined_samples = []

if os.path.exists(raw_messages_path):
    for json_file in glob.glob(f'{raw_messages_path}/*.json'):
        try:
            with open(json_file, 'r') as f:
                messages = json.load(f)
            
            for msg in messages:
                txt = msg.get('text', '').lower() if isinstance(msg, dict) else ''
                
                # Check for unethical keywords
                if any(k in txt for k in unethical_keywords):
                    # Get full text
                    full_text = msg.get('text', '') if isinstance(msg, dict) else ''
                    if len(full_text) > 20:  # Skip very short
                        mined_samples.append({
                            'text': full_text,
                            'label': 'Unethical',
                            'source': 'mined',
                            'fixed_by': 'unethical_mining'
                        })
        except:
            continue

# Deduplicate
unique_mined = list({s['text']: s for s in mined_samples}.values())
print(f'   Found {len(unique_mined)} unique unethical samples from raw messages')

# Add to dataset
data.extend(unique_mined[:50])  # Add up to 50 samples

# ========== 3. Save ==========
with open(file_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'\n✅ Done! Added Unethical samples to dataset.')

# Show distribution
from collections import Counter
labels = Counter(d['label'] for d in data)
print('\n📊 New Distribution:')
for lbl, cnt in labels.most_common():
    print(f'   {lbl}: {cnt}')
