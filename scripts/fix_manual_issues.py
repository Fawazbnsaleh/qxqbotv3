#!/usr/bin/env python3
"""
FIX MANUAL REVIEW ISSUES
Based on manual verification findings:
1. Hacking: Remove gaming servers, password questions, student jokes
2. Unethical: Remove normal questions, spam
3. Normal: Move hidden services to correct categories
"""
import json
from collections import Counter

print('🔧 FIXING MANUAL REVIEW ISSUES')
print('=' * 70)

file_path = 'al_rased/data/labeledSamples/training_data.json'
with open(file_path, 'r') as f:
    data = json.load(f)

fixes = {
    'hacking_to_normal': 0,
    'hacking_to_spam': 0,
    'unethical_to_normal': 0,
    'unethical_to_spam': 0,
    'normal_to_medical': 0,
    'normal_to_academic': 0,
}

# ========== 1. FIX HACKING ==========
print('\n🔓 1. Fixing Hacking Category...')

# Patterns that are NOT hacking
gaming_patterns = ['سيرفر', 'كرافت', 'minecraft', 'ماين', 'تيمات', 'فكرة السيرفر']
spam_patterns = ['متوفر توثيق', 'متوفر يوزرات', 'رصيد نون', 'قسايم', 'شحن']
question_patterns = ['كيف', 'اريد شرح', 'ممكن', 'انسحبت', 'ورجعت', 'ما بغير', 'تتهكر درجاتي']
true_hacking = ['تهكير', 'اختراق', 'هكر', 'سرقة حساب', 'سحب معلومات', 'فك حماية', 'تجسس']

for d in data:
    if d.get('label') != 'Hacking':
        continue
    
    txt = d.get('text', '').lower()
    
    # Check if it's a gaming server -> Spam
    if any(p in txt for p in gaming_patterns):
        if not any(h in txt for h in true_hacking):
            d['label'] = 'Spam'
            d['fixed_by'] = 'manual_review_fix'
            fixes['hacking_to_spam'] += 1
            continue
    
    # Check if it's spam (not hacking service)
    if any(p in txt for p in spam_patterns):
        if not any(h in txt for h in true_hacking):
            d['label'] = 'Spam'
            d['fixed_by'] = 'manual_review_fix'
            fixes['hacking_to_spam'] += 1
            continue
    
    # Check if it's a question -> Normal
    if any(p in txt for p in question_patterns):
        if not any(h in txt for h in true_hacking):
            d['label'] = 'Normal'
            d['fixed_by'] = 'manual_review_fix'
            fixes['hacking_to_normal'] += 1
            continue

print(f'   Hacking -> Normal: {fixes["hacking_to_normal"]}')
print(f'   Hacking -> Spam: {fixes["hacking_to_spam"]}')

# ========== 2. FIX UNETHICAL ==========
print('\n🔞 2. Fixing Unethical Category...')

# Patterns that are NOT unethical
normal_questions = ['مين تخصصه', 'اريد', 'ابي', 'كم سعر', 'شلون', 'كيف']
spam_in_unethical = ['بيع معرفات', 'رفع منصات', 'تفعيل مميز', 'يوزرات']
true_unethical = ['سكس', 'porn', 'xxx', 'نيك', 'هيجانه', 'نودز', 'تحرش', 'اطفال', 'حشيش', 'مخدرات']

for d in data:
    if d.get('label') != 'Unethical':
        continue
    
    txt = d.get('text', '').lower()
    
    # Skip if it has true unethical content
    if any(u in txt for u in true_unethical):
        continue
    
    # Check if it's spam
    if any(p in txt for p in spam_in_unethical):
        d['label'] = 'Spam'
        d['fixed_by'] = 'manual_review_fix'
        fixes['unethical_to_spam'] += 1
        continue
    
    # Check if it's a normal question
    if any(p in txt for p in normal_questions) and len(txt) < 200:
        d['label'] = 'Normal'
        d['fixed_by'] = 'manual_review_fix'
        fixes['unethical_to_normal'] += 1
        continue
    
    # If it doesn't have true unethical keywords, move to Normal
    if not any(u in txt for u in true_unethical):
        d['label'] = 'Normal'
        d['fixed_by'] = 'manual_review_fix'
        fixes['unethical_to_normal'] += 1

print(f'   Unethical -> Normal: {fixes["unethical_to_normal"]}')
print(f'   Unethical -> Spam: {fixes["unethical_to_spam"]}')

# ========== 3. FIX NORMAL (Hidden Services) ==========
print('\n🟢 3. Fixing Normal (Hidden Services)...')

# Services that should NOT be in Normal
medical_services = ['سكليف', 'اجازة مرضية', 'عذر طبي', 'تقرير مرضي']
academic_services = ['حل واجبات', 'نحل واجبات', 'حل مشاريع', 'كتابة بحوث']

# Words that indicate it's just a question/request (keep in Normal)
question_words = ['ابي', 'ابغى', 'اريد', 'مين يعرف', 'محتاج']

for d in data:
    if d.get('label') != 'Normal':
        continue
    
    txt = d.get('text', '').lower()
    
    # Check if it's an ACTIVE service (not a request)
    is_question = any(q in txt for q in question_words)
    is_service = any(s in txt for s in ['متوفر', 'شغال الان', 'التعاب بعد الانجاز', 'تحويل بعد'])
    
    if is_service and not is_question:
        # Medical service
        if any(m in txt for m in medical_services):
            d['label'] = 'Medical Fraud'
            d['fixed_by'] = 'manual_review_fix'
            fixes['normal_to_medical'] += 1
            continue
        
        # Academic service
        if any(a in txt for a in academic_services):
            d['label'] = 'Academic Cheating'
            d['fixed_by'] = 'manual_review_fix'
            fixes['normal_to_academic'] += 1
            continue

print(f'   Normal -> Medical Fraud: {fixes["normal_to_medical"]}')
print(f'   Normal -> Academic Cheating: {fixes["normal_to_academic"]}')

# ========== SAVE ==========
with open(file_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# ========== SUMMARY ==========
print('\n' + '=' * 70)
total = sum(fixes.values())
print(f'✅ TOTAL FIXES: {total}')

# Show new distribution
labels = Counter(d['label'] for d in data)
print('\n📊 Updated Distribution:')
for lbl, cnt in labels.most_common():
    print(f'   {lbl}: {cnt}')
