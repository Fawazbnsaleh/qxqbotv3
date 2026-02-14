#!/usr/bin/env python3
"""Comprehensive Dataset Audit Script"""
import json
from collections import Counter

print('📊 COMPREHENSIVE DATASET AUDIT')
print('=' * 70)

with open('al_rased/data/labeledSamples/training_data.json', 'r') as f:
    data = json.load(f)

print(f'Total Samples: {len(data)}')

# ========== 1. Category Distribution ==========
print('\n📈 1. Category Distribution')
labels = Counter(d.get('label', '') for d in data)
for lbl, cnt in labels.most_common():
    print(f'   {lbl}: {cnt}')

# ========== 2. Duplicate Check ==========
print('\n🔁 2. Duplicate Check')
text_counts = Counter(d.get('text', '') for d in data)
duplicates = [(txt, cnt) for txt, cnt in text_counts.items() if cnt > 1]
print(f'   Unique Texts: {len(text_counts)}')
print(f'   Duplicated Texts: {len(duplicates)}')

# ========== 3. Short Samples ==========
print('\n📏 3. Short Samples (< 20 chars)')
short = [d for d in data if len(d.get('text', '')) < 20]
print(f'   Found: {len(short)}')
for d in short[:3]:
    lbl = d.get('label', '')
    txt = d.get('text', '')
    print(f'   [{lbl}] "{txt}"')

# ========== 4. Academic Cheating Purity ==========
print('\n🎓 4. Academic Cheating Purity')
cheating = [d for d in data if d.get('label') == 'Academic Cheating']
non_academic = ['binance', 'usdt', 'crypto', 'forex', 'مفسر احلام', 'زواج', 'مظلات', 'خادمة']
impure = [d for d in cheating if any(k in d.get('text', '').lower() for k in non_academic)]
q_words = ['مين يحل', 'ابي احد', 'ممكن احد', 'شلون اسوي', 'كيف احصل']
students = [d for d in cheating if any(k in d.get('text', '').lower() for k in q_words)]
print(f'   Total: {len(cheating)} | Non-Academic: {len(impure)} | Student Q: {len(students)}')

# ========== 5. Normal Purity ==========
print('\n🟢 5. Normal Purity')
normal = [d for d in data if d.get('label') == 'Normal']
service_kw = ['حل واجبات', 'سكليف', 'اجازات مرضية', 'استثمر معي', 'ارباح', 'للتواصل خاص']
hidden_services = [d for d in normal if any(k in d.get('text', '').lower() for k in service_kw)]
print(f'   Total: {len(normal)} | Hidden Services: {len(hidden_services)}')

# ========== 6. Medical Fraud Purity ==========
print('\n🏥 6. Medical Fraud Purity')
medical = [d for d in data if d.get('label') == 'Medical Fraud']
academic_in_med = [d for d in medical if 'واجب' in d.get('text', '').lower() or 'بحث' in d.get('text', '').lower()]
print(f'   Total: {len(medical)} | Academic Keywords: {len(academic_in_med)}')

# ========== 7. Financial Scams Purity ==========
print('\n💰 7. Financial Scams Purity')
financial = [d for d in data if d.get('label') == 'Financial Scams']
normal_chat = [d for d in financial if 'شكرا' in d.get('text', '').lower() and len(d.get('text', '')) < 30]
print(f'   Total: {len(financial)} | Short Thank-You: {len(normal_chat)}')

# ========== 8. Hacking Purity ==========
print('\n🔓 8. Hacking Purity')
hacking = [d for d in data if d.get('label') == 'Hacking']
news_kw = ['ثغرة امنية', 'اكتشاف ثغرة', 'تحذير امني']
news = [d for d in hacking if any(k in d.get('text', '').lower() for k in news_kw)]
print(f'   Total: {len(hacking)} | Security News: {len(news)}')

# ========== 9. Spam Purity ==========
print('\n📢 9. Spam Purity')
spam = [d for d in data if d.get('label') == 'Spam']
greetings = [d for d in spam if len(d.get('text', '')) < 15]
print(f'   Total: {len(spam)} | Very Short: {len(greetings)}')

# ========== SUMMARY ==========
print('\n' + '=' * 70)
issues = len(impure) + len(students) + len(hidden_services) + len(academic_in_med) + len(normal_chat) + len(news) + len(greetings) + len(duplicates) + len(short)
print(f'📋 TOTAL ISSUES: {issues}')
print(f'   - Duplicates: {len(duplicates)}')
print(f'   - Short Samples: {len(short)}')
print(f'   - Cross-Category Leaks: {len(impure) + len(academic_in_med) + len(news)}')
print(f'   - Hidden Students/Sellers: {len(students) + len(hidden_services)}')
print(f'   - Noise (Short thank-you/greetings): {len(normal_chat) + len(greetings)}')
