#!/usr/bin/env python3
"""
COMPREHENSIVE FIX: All Remaining Issues
- Remove duplicates
- Fix short samples 
- Fix hidden services in Normal
- Fix cross-category leaks
- Fix questions in violations
"""
import json
from collections import Counter

print('🛠️ COMPREHENSIVE FIX: All Remaining Issues')
print('=' * 70)

file_path = 'al_rased/data/labeledSamples/training_data.json'
with open(file_path, 'r') as f:
    data = json.load(f)

original_count = len(data)
fixes = {
    'duplicates_removed': 0,
    'short_removed': 0,
    'hidden_services_fixed': 0,
    'cross_category_fixed': 0,
    'questions_fixed': 0,
}

# ========== 1. REMOVE DUPLICATES ==========
print('\n🔁 1. Removing Duplicates...')
seen_texts = set()
unique_data = []
for d in data:
    txt = d.get('text', '')
    if txt not in seen_texts:
        seen_texts.add(txt)
        unique_data.append(d)
    else:
        fixes['duplicates_removed'] += 1
data = unique_data
print(f'   Removed: {fixes["duplicates_removed"]}')

# ========== 2. FIX SHORT SAMPLES ==========
print('\n📏 2. Fixing Short Samples (< 15 chars)...')
# Keep short samples ONLY if they have strong keywords
strong_keywords = ['سكس', 'سكليف', 'تهكير', 'حشيش', 'اختراق']
filtered_data = []
for d in data:
    txt = d.get('text', '')
    if len(txt) < 15:
        has_strong = any(k in txt.lower() for k in strong_keywords)
        if not has_strong:
            fixes['short_removed'] += 1
            continue  # Remove
    filtered_data.append(d)
data = filtered_data
print(f'   Removed: {fixes["short_removed"]}')

# ========== 3. FIX HIDDEN SERVICES IN NORMAL ==========
print('\n🟢 3. Fixing Hidden Services in Normal...')
service_patterns = {
    'Academic Cheating': ['حل واجبات', 'نحل واجبات', 'حل مشاريع', 'كتابة بحوث', 'حل اختبارات'],
    'Medical Fraud': ['سكليف', 'اجازة مرضية', 'اجازات مرضية', 'عذر طبي'],
    'Financial Scams': ['استثمر معي', 'ارباح يومية', 'ارباح مضمونة', 'فرصة استثمارية'],
}
student_keywords = ['ابي', 'ابغى', 'مين', 'ممكن', 'احتاج', 'وين', 'كيف']

for d in data:
    if d.get('label') != 'Normal':
        continue
    
    txt = d.get('text', '').lower()
    
    # Check if it's a student asking (NOT a service)
    is_student = any(k in txt for k in student_keywords)
    
    for category, patterns in service_patterns.items():
        if any(p in txt for p in patterns):
            # Only fix if NOT a student question
            if not is_student or 'للتواصل' in txt or 'متوفر' in txt:
                d['label'] = category
                d['fixed_by'] = 'comprehensive_fix_hidden_service'
                fixes['hidden_services_fixed'] += 1
                break

print(f'   Fixed: {fixes["hidden_services_fixed"]}')

# ========== 4. FIX CROSS-CATEGORY LEAKS ==========
print('\n🏥 4. Fixing Cross-Category Leaks...')

for d in data:
    txt = d.get('text', '').lower()
    label = d.get('label', '')
    
    # Medical Fraud with pure Academic content -> Academic Cheating
    if label == 'Medical Fraud':
        has_academic = any(k in txt for k in ['واجب', 'بحث', 'مشروع تخرج', 'رسالة ماجستير'])
        has_medical = any(k in txt for k in ['سكليف', 'اجازة', 'صحتي', 'طبي', 'مستشفى'])
        
        if has_academic and not has_medical:
            d['label'] = 'Academic Cheating'
            d['fixed_by'] = 'comprehensive_fix_cross_category'
            fixes['cross_category_fixed'] += 1

print(f'   Fixed: {fixes["cross_category_fixed"]}')

# ========== 5. FIX QUESTIONS IN VIOLATIONS ==========
print('\n❓ 5. Fixing Questions in Violations...')
question_patterns = ['مين يعرف', 'ابي احد', 'كيف اقدر', 'وين احصل', 'ممكن احد يساعد', 'احتاج مساعدة']

for d in data:
    label = d.get('label', '')
    if label in ['Normal', 'Unethical', 'Hacking']:
        continue  # Skip Normal and keyword-based categories
    
    txt = d.get('text', '').lower()
    
    # Check if it looks like a question
    is_question = any(q in txt for q in question_patterns)
    
    # Check if it's NOT a disguised service
    is_service = any(s in txt for s in ['للتواصل', 'متوفر', 'يوجد لدينا', 'تواصل معي', 'خاص'])
    
    if is_question and not is_service:
        d['label'] = 'Normal'
        d['fixed_by'] = 'comprehensive_fix_question'
        fixes['questions_fixed'] += 1

print(f'   Fixed: {fixes["questions_fixed"]}')

# ========== SAVE ==========
print('\n' + '=' * 70)
with open(file_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

total_fixes = sum(fixes.values())
print(f'✅ COMPREHENSIVE FIX COMPLETE')
print(f'   Original Samples: {original_count}')
print(f'   Final Samples: {len(data)}')
print(f'   Total Fixes: {total_fixes}')
print('')
for key, count in fixes.items():
    if count > 0:
        print(f'   - {key}: {count}')

# Show new distribution
print('\n📊 New Distribution:')
labels = Counter(d['label'] for d in data)
for lbl, cnt in labels.most_common():
    print(f'   {lbl}: {cnt}')
