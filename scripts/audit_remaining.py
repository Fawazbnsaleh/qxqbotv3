
import json
import re
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔍 Auditing Remaining Categories (Financial, Unethical, Hacking, Spam)...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # 1. Financial Scams Audit
    # Look for "Normal" banking questions or legit trading discussions
    fin_suspects = []
    for i, d in enumerate(data):
        if 'Financial Scams' in d.get('labels', []):
            text = d['text']
            # Suspicious if purely a question about bank procedures without scam keywords
            if 'كيف' in text and any(kw in text for kw in ['بنك', 'حوالة', 'صراف']) and not any(kw in text for kw in ['ربح', 'استثمار', 'مضمون', 'محفظة']):
                 fin_suspects.append({'text': text[:50], 'cat': 'Financial'})

    # 2. Unethical Audit
    # Look for Academic Services mislabeled as Unethical (very common error)
    unethical_academic = []
    for i, d in enumerate(data):
        if 'Unethical' in d.get('labels', []):
            text = d['text']
            if any(kw in text for kw in ['خدمات طلابية', 'بحث', 'مشروع', 'تخرج', 'رسالة', 'ماجستير']):
                unethical_academic.append({'text': text[:50], 'cat': 'Unethical -> Academic'})

    # 3. Hacking Audit
    # Look for Spam (Game servers) or Financial (Crypto scams)
    hacking_suspects = []
    for i, d in enumerate(data):
        if 'Hacking' in d.get('labels', []):
            text = d['text']
            if 'ماين كرافت' in text or 'سيرفر' in text:
                hacking_suspects.append({'text': text[:50], 'cat': 'Hacking -> Spam (Game)'})
            elif 'استثمار' in text or 'usdt' in text.lower():
                hacking_suspects.append({'text': text[:50], 'cat': 'Hacking -> Financial'})

    # 4. Spam Audit
    # Look for legit appearing messages classified as spam
    spam_legit = []
    for i, d in enumerate(data):
        if 'Spam' in d.get('labels', []):
            text = d['text']
            if len(text) > 50 and 'كيف' in text and not any(kw in text for kw in ['رابط', 'انضم', 'بيع', 'عرض']):
                 spam_legit.append({'text': text[:50], 'cat': 'Spam -> Normal?'})


    print(f"\n💰 Financial Scams Suspicious: {len(fin_suspects)}")
    for s in fin_suspects: print(f"   - {s['text']}...")

    print(f"\n🔞 Unethical -> Academic Suspects: {len(unethical_academic)}")
    for s in unethical_academic: print(f"   - {s['text']}...")

    print(f"\n🔓 Hacking Suspects: {len(hacking_suspects)}")
    for s in hacking_suspects: print(f"   - [{s['cat']}] {s['text']}...")
    
    print(f"\n📢 Spam -> Legit? Suspects: {len(spam_legit)}")
    for s in spam_legit[:10]: print(f"   - {s['text']}...")

if __name__ == "__main__":
    main()
