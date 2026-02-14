
import json
import re
import os
import sys
from collections import Counter, defaultdict

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define the keywords we are using (merged from previous steps)
KEYWORDS = {
    'Academic Cheating': [
        'حل واجب', 'حل اختبار', 'مشاريع تخرج', 'رسائل ماجستير', 
        'اعداد بحوث', 'خدمات طلابية', 'اسايمنت', 'كويزات', 'تسميع',
        'مساعدة في الاختبار', 'أبحاث جامعية', 'امتحانت', 'اساينمنت', 'بروجكت'
    ],
    'Medical Fraud': [
        'سكليف', 'اجازة مرضية', 'تقرير طبي', 'عذر طبي', 'مشهد مرافقة',
        'مستشفى حكومي', 'منصة صحتي', 'مرضيه معتمده', 'اجازه مرضيه', 'سك ليف'
    ],
    'Financial Scams': [
        'ارباح مضمونة', 'تداول', 'فوركس', 'عملات رقمية', 'ادارة محافظ', 
        'ربح يومي', 'دخل اضافي', 'توصيات ذهب', 'crypto', 'bitcoin', 'usdt', 
        'binance', 'investment', 'profit', 'بيتكوين'
    ],
    'Hacking': [
        'تهكير', 'اختراق', 'تجسس', 'سحب صور', 'استرداد حساب',
        'زيادة متابعين', 'توثيق حساب', 'رشق'
    ],
    'Unethical': [
        'سكس', 'ممحون', 'ديوث', 'قحبة', 'سهرات', 'مساج', 'حشيش', 
        'مخدرات', 'كبتاجون', 'شبو', 'نودز', 'افلام اباحية'
    ],
    'Spam': [
        'سيرفر ماينكرافت', 'تبادل نشر', 'اشترك في قناتنا', 'ارقام وهمية', 'تفعيل تليجرام'
    ]
}

def check_keywords(text):
    text = text.lower()
    found = []
    for cat, kws in KEYWORDS.items():
        for kw in kws:
            if kw in text:
                found.append((cat, kw))
    return found

def main():
    print("🔍 Analyzing Keyword Issues...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Stats
    keyword_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'false_positive': 0, 'fp_samples': []})
    conflicts = []

    for sample in data:
        text = sample['text']
        # Normalize labels to list
        current_labels = sample.get('labels', [sample.get('label', 'Normal')])
        if isinstance(current_labels, str): current_labels = [current_labels]
        
        # Check against our keyword list
        matches = check_keywords(text)
        
        # 1. Check for Conflicts (Keywords from different categories in same text)
        cats_found = set(m[0] for m in matches)
        if len(cats_found) > 1:
            conflicts.append({
                'text': text[:50],
                'cats': list(cats_found),
                'matches': [m[1] for m in matches]
            })

        # 2. Check Effectiveness
        for cat, kw in matches:
            stats_key = f"{cat}:{kw}"
            keyword_stats[stats_key]['total'] += 1
            
            if cat in current_labels:
                keyword_stats[stats_key]['correct'] += 1
            else:
                keyword_stats[stats_key]['false_positive'] += 1
                if len(keyword_stats[stats_key]['fp_samples']) < 3:
                    keyword_stats[stats_key]['fp_samples'].append({
                        'text': text[:40],
                        'actual_label': current_labels
                    })

    # Report
    print("\n⚠️ Problematic Keywords (High False Positive Rate > 20%):")
    print(f"| {'Keyword':<20} | {'Category':<15} | {'Total':<5} | {'FP':<5} | {'Rate':<5} | {'Example Mismatch'}")
    print("|" + "-"*22 + "|" + "-"*17 + "|" + "-"*7 + "|" + "-"*7 + "|" + "-"*7 + "|" + "-"*30)
    
    found_issues = False
    for key, stats in keyword_stats.items():
        if stats['total'] > 5: # Ignore rare keywords
            fp_rate = stats['false_positive'] / stats['total']
            if fp_rate > 0.2:
                found_issues = True
                cat, kw = key.split(':')
                example = str(stats['fp_samples'][0]['actual_label']) if stats['fp_samples'] else ""
                print(f"| {kw:<20} | {cat:<15} | {stats['total']:<5} | {stats['false_positive']:<5} | {fp_rate:.0%} | {example}")

    if not found_issues:
        print("✅ No major keyword issues found (all FP rates < 20%)")

    print("\n⚔️ Conflicting Keywords (Samples matching multiple categories):")
    print(f"Found {len(conflicts)} samples with conflicting keywords.")
    if conflicts:
        print("Examples:")
        for c in conflicts[:5]:
            print(f"- {c['cats']} (Keywords: {c['matches']}): '{c['text']}...'")

if __name__ == "__main__":
    main()
