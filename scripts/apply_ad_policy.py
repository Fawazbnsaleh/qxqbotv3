#!/usr/bin/env python3
"""
Reclassify samples based on user policy: ALL ADS ARE VIOLATIONS
Move to appropriate category based on content.
"""
import json

print('🔄 Reclassifying Based on "All Ads = Violation" Policy')
print('=' * 70)

file_path = 'al_rased/data/labeledSamples/training_data.json'
with open(file_path, 'r') as f:
    data = json.load(f)

fixes = {
    'hacking_to_normal': 0,
    'hacking_to_financial': 0,
    'hacking_to_academic': 0,
    'hacking_to_spam': 0,
    'financial_to_normal': 0,
    'spam_to_normal': 0,
    'normal_to_spam': 0,
}

for d in data:
    txt = d.get('text', '').lower()
    label = d.get('label', '')
    
    # ========== Fix HACKING Category ==========
    if label == 'Hacking':
        # Crypto news/analysis -> Financial Scams or Normal
        if any(k in txt for k in ['binance', 'بتكوين', 'bitcoin', 'عملة', 'منصة', 'إدراج']):
            if any(k in txt for k in ['استثمار', 'ارباح', 'ربح', 'فرصة']):
                d['label'] = 'Financial Scams'
                d['fixed_by'] = 'policy_all_ads_violation'
                fixes['hacking_to_financial'] += 1
            else:
                d['label'] = 'Normal'  # Just crypto news
                d['fixed_by'] = 'policy_all_ads_violation'
                fixes['hacking_to_normal'] += 1
        
        # Gaming servers (Minecraft, etc.) -> Spam (it's an ad)
        elif any(k in txt for k in ['سيرفر', 'server', 'ماين كرافت', 'minecraft', 'lord craft', 'كرافت']):
            d['label'] = 'Spam'
            d['fixed_by'] = 'policy_all_ads_violation'
            fixes['hacking_to_spam'] += 1
        
        # Academic services misplaced -> Academic Cheating
        elif any(k in txt for k in ['مشروع تخرج', 'بحوث', 'واجبات', 'رسالة ماجستير']):
            d['label'] = 'Academic Cheating'
            d['fixed_by'] = 'policy_all_ads_violation'
            fixes['hacking_to_academic'] += 1
        
        # Technical advice (not selling) -> Normal
        elif any(k in txt for k in ['كيف', 'طريقة', 'يمكن', 'استرجاع']) and 'للتواصل' not in txt:
            d['label'] = 'Normal'
            d['fixed_by'] = 'policy_all_ads_violation'
            fixes['hacking_to_normal'] += 1
        
        # Bot services -> Spam
        elif any(k in txt for k in ['متوفر عمل بوت', 'بوت اعلانات', 'بوت للمزاد']):
            d['label'] = 'Spam'
            d['fixed_by'] = 'policy_all_ads_violation'
            fixes['hacking_to_spam'] += 1
    
    # ========== Fix FINANCIAL SCAMS: Questions -> Normal ==========
    if label == 'Financial Scams':
        # Someone genuinely asking for help
        if any(k in txt for k in ['أنا متداول مبتدئ', 'كيف اتعلم', 'وين اتعلم', 'ابحث عن مصادر']):
            if 'للتواصل' not in txt and 'خاص' not in txt:
                d['label'] = 'Normal'
                d['fixed_by'] = 'policy_all_ads_violation'
                fixes['financial_to_normal'] += 1
    
    # ========== Fix SPAM: Questions -> Normal ==========
    if label == 'Spam':
        # Someone asking a question (not advertising)
        if any(k in txt for k in ['حد يعرف', 'مين يعرف', 'كيف', 'وين']) and len(txt) < 100:
            if 'للتواصل' not in txt and 'خاص' not in txt:
                d['label'] = 'Normal'
                d['fixed_by'] = 'policy_all_ads_violation'
                fixes['spam_to_normal'] += 1

# Save
with open(file_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('\n📊 Reclassification Summary:')
total = 0
for key, count in fixes.items():
    if count > 0:
        print(f'   {key}: {count}')
        total += count
print(f'\n✅ Total Reclassified: {total}')
