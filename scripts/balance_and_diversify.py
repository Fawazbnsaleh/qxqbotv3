#!/usr/bin/env python3
"""
BALANCE & DIVERSIFY DATASET
1. Intensive mining for weak categories
2. Reduce Normal class to improve balance
3. Remove over-duplicated samples
"""
import json
import os
import glob
import random
from collections import Counter

print('⚖️ BALANCING & DIVERSIFYING DATASET')
print('=' * 70)

# ========== 1. INTENSIVE MINING ==========
print('\n📥 1. INTENSIVE MINING FOR WEAK CATEGORIES')
print('-' * 40)

# Extended patterns with more variety
mining_patterns = {
    'Hacking': [
        # Arabic hacking services
        'هكر', 'تهكير', 'اختراق', 'سرقة حساب', 'فك حماية',
        'حظر حساب', 'فتح حساب محظور', 'سحب معلومات', 'تجسس',
        'باسورد', 'كلمة سر', 'رمز التحقق', 'كود التفعيل',
        # English hacking terms
        'hack', 'hacker', 'crack', 'bypass', 'bruteforce',
        # Platform-specific
        'واتس هكر', 'انستا هكر', 'تليجرام هكر', 'سناب هكر',
    ],
    'Spam': [
        # Followers/Likes services
        'زيادة متابعين', 'رشق متابعين', 'شراء متابعين', 'متابعين وهميين',
        'زيادة لايكات', 'زيادة مشاهدات', 'ترويج حساب',
        # Subscription services
        'اشتراكات', 'نتفلكس', 'شاهد', 'spotify', 'iptv',
        # Generic spam
        'شحن جواهر', 'شحن شدات', 'شحن الماس', 'شحن uc',
        # Ads
        'للاعلان', 'للإعلان', 'اعلانات', 'دعاية',
    ],
    'Financial Scams': [
        # Investment scams
        'استثمار مضمون', 'ارباح يومية', 'ارباح مضمونة', 'عوائد',
        'تداول', 'فوركس', 'forex', 'ربح سريع', 'ثروة',
        # Job scams
        'وظيفة من المنزل', 'راتب بدون عمل', 'دخل اضافي',
        # Crypto scams
        'عملات رقمية', 'بتكوين', 'ايثريوم', 'عملة جديدة',
    ],
}

# Load current data
file_path = 'al_rased/data/labeledSamples/training_data.json'
with open(file_path, 'r') as f:
    data = json.load(f)

existing_texts = {d['text'] for d in data}
mined_counts = {cat: 0 for cat in mining_patterns}

# Search in group_messages
group_messages_path = 'al_rased/data/group_messages'
if os.path.exists(group_messages_path):
    json_files = glob.glob(f'{group_messages_path}/*.json')
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                messages = json.load(f)
            
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                
                txt = msg.get('text', '')
                txt_lower = txt.lower()
                
                if len(txt) < 30 or txt in existing_texts:
                    continue
                
                # Check for patterns - must be a SERVICE not a question
                is_question = any(q in txt_lower for q in ['مين يعرف', 'ابي', 'ابغى', 'كيف'])
                is_service = any(s in txt_lower for s in ['متوفر', 'للتواصل', 'يوجد لدينا', 'خاص', 'dm', 'للطلب'])
                
                if is_question and not is_service:
                    continue
                
                for category, patterns in mining_patterns.items():
                    if any(p in txt_lower for p in patterns):
                        data.append({
                            'text': txt,
                            'label': category,
                            'source': 'intensive_mining'
                        })
                        existing_texts.add(txt)
                        mined_counts[category] += 1
                        break
        except:
            continue

for cat, count in mined_counts.items():
    if count > 0:
        print(f'   {cat}: +{count} new samples')

# ========== 2. REDUCE NORMAL CLASS ==========
print('\n📉 2. REDUCING NORMAL CLASS (Target: 1000)')
print('-' * 40)

normal_samples = [d for d in data if d['label'] == 'Normal']
other_samples = [d for d in data if d['label'] != 'Normal']

# Keep diverse Normal samples (prioritize longer, more diverse ones)
random.shuffle(normal_samples)  # Shuffle first to avoid bias
normal_samples.sort(key=lambda x: len(x['text']), reverse=True)  # Keep longer ones

# Keep top 1000
target_normal = 1000
if len(normal_samples) > target_normal:
    removed = len(normal_samples) - target_normal
    normal_samples = normal_samples[:target_normal]
    print(f'   Reduced Normal: {len(normal_samples) + removed} -> {len(normal_samples)} (-{removed})')
else:
    print(f'   Normal already at {len(normal_samples)} (no reduction needed)')

data = other_samples + normal_samples

# ========== 3. REMOVE OVER-DUPLICATED ==========
print('\n🔁 3. REMOVING EXCESSIVE DUPLICATES')
print('-' * 40)

# For upsampled categories, limit duplicates to max 2x original
for cat in ['Hacking', 'Spam', 'Unethical']:
    cat_samples = [d for d in data if d['label'] == cat]
    original = [d for d in cat_samples if not d.get('is_augmented') and not d.get('upsampled_by')]
    augmented = [d for d in cat_samples if d.get('is_augmented') or d.get('upsampled_by')]
    
    # Max augmented = 2x original
    max_augmented = len(original) * 2
    if len(augmented) > max_augmented:
        removed = len(augmented) - max_augmented
        augmented = random.sample(augmented, max_augmented)
        print(f'   {cat}: Reduced augmented from {len(augmented) + removed} to {len(augmented)} (-{removed})')
        
        # Rebuild data
        other = [d for d in data if d['label'] != cat]
        data = other + original + augmented

# ========== SAVE ==========
with open(file_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# ========== FINAL STATS ==========
print('\n' + '=' * 70)
print('📊 FINAL DISTRIBUTION:')
labels = Counter(d['label'] for d in data)
total = len(data)
for lbl, cnt in labels.most_common():
    pct = cnt / total * 100
    bar = '█' * int(pct / 2)
    print(f'   {lbl:20} {cnt:5} ({pct:5.1f}%) {bar}')

# Balance score
min_count = min(labels.values())
max_count = max(labels.values())
balance = min_count / max_count * 100
print(f'\n⚖️ Balance Ratio: {balance:.1f}%')
