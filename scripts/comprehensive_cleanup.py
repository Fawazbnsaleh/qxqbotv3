#!/usr/bin/env python3
"""Comprehensive Dataset Cleanup Script"""
import json
from collections import Counter

print('🧹 COMPREHENSIVE DATASET CLEANUP')
print('=' * 70)

file_path = 'al_rased/data/labeledSamples/training_data.json'
with open(file_path, 'r') as f:
    data = json.load(f)

original_count = len(data)
fixes = 0

# ========== 1. Remove Duplicates (Keep first occurrence) ==========
print('\n🔁 1. Removing Duplicates...')
seen_texts = set()
unique_data = []
duplicates_removed = 0
for d in data:
    txt = d.get('text', '')
    if txt not in seen_texts:
        seen_texts.add(txt)
        unique_data.append(d)
    else:
        duplicates_removed += 1
data = unique_data
print(f'   Removed: {duplicates_removed} duplicates')
fixes += duplicates_removed

# ========== 2. Remove Very Short Samples (< 15 chars, unless strong keywords) ==========
print('\n📏 2. Removing Very Short Samples...')
strong_keywords = ['حل', 'سكليف', 'تهكير', 'احتيال']
short_removed = 0
filtered_data = []
for d in data:
    txt = d.get('text', '')
    if len(txt) < 15:
        has_strong = any(k in txt for k in strong_keywords)
        if not has_strong:
            short_removed += 1
            continue  # Skip this sample
    filtered_data.append(d)
data = filtered_data
print(f'   Removed: {short_removed} short samples')
fixes += short_removed

# ========== 3. Fix Cross-Category Leaks: Non-Academic in Cheating -> Appropriate ==========
print('\n🎓 3. Fixing Non-Academic in Cheating...')
non_academic = ['binance', 'usdt', 'crypto', 'forex', 'مفسر احلام', 'زواج', 'مظلات', 'خادمة']
non_acad_fixed = 0
for d in data:
    if d.get('label') == 'Academic Cheating':
        txt = d.get('text', '').lower()
        if any(k in txt for k in ['binance', 'usdt', 'crypto', 'forex', 'تداول', 'ارباح']):
            d['label'] = 'Financial Scams'
            d['fixed_by'] = 'comprehensive_cleanup'
            non_acad_fixed += 1
        elif any(k in txt for k in ['مفسر احلام', 'زواج', 'مظلات', 'خادمة']):
            d['label'] = 'Normal'
            d['fixed_by'] = 'comprehensive_cleanup'
            non_acad_fixed += 1
print(f'   Fixed: {non_acad_fixed} samples')
fixes += non_acad_fixed

# ========== 4. Fix Academic Keywords in Medical Fraud -> Move to Cheating ==========
print('\n🏥 4. Fixing Academic in Medical Fraud...')
# Only move if it looks like academic service, not medical
acad_in_med_fixed = 0
for d in data:
    if d.get('label') == 'Medical Fraud':
        txt = d.get('text', '').lower()
        has_academic = 'واجب' in txt or 'بحث' in txt or 'مشروع' in txt
        has_medical = 'سكليف' in txt or 'اجازة' in txt or 'صحتي' in txt or 'طبي' in txt
        if has_academic and not has_medical:
            d['label'] = 'Academic Cheating'
            d['fixed_by'] = 'comprehensive_cleanup'
            acad_in_med_fixed += 1
print(f'   Fixed: {acad_in_med_fixed} samples')
fixes += acad_in_med_fixed

# ========== 5. Fix Hidden Services in Normal ==========
print('\n🟢 5. Fixing Hidden Services in Normal...')
service_kw = ['حل واجبات', 'سكليف', 'اجازات مرضية', 'استثمر معي', 'ارباح يومية', 'للتواصل خاص']
student_kw = ['ابي', 'ابغى', 'مين', 'ممكن', 'احتاج']
hidden_fixed = 0
for d in data:
    if d.get('label') == 'Normal':
        txt = d.get('text', '').lower()
        if any(k in txt for k in service_kw):
            is_student = any(k in txt for k in student_kw)
            if not is_student:
                # Determine correct category
                if 'سكليف' in txt or 'اجازات مرضية' in txt:
                    d['label'] = 'Medical Fraud'
                elif 'استثمر' in txt or 'ارباح' in txt:
                    d['label'] = 'Financial Scams'
                else:
                    d['label'] = 'Academic Cheating'
                d['fixed_by'] = 'comprehensive_cleanup'
                hidden_fixed += 1
print(f'   Fixed: {hidden_fixed} samples')
fixes += hidden_fixed

# ========== Save ==========
print('\n' + '=' * 70)
with open(file_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'✅ CLEANUP COMPLETE')
print(f'   Original Samples: {original_count}')
print(f'   Final Samples: {len(data)}')
print(f'   Total Fixes: {fixes}')
