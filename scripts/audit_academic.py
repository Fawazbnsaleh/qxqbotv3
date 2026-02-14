
import json
import re
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🎓 Auditing 'Academic Cheating' Samples...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Filter Academic Cheating
    academic_samples = [d for d in data if 'Academic Cheating' in d.get('labels', [d.get('label')])]
    print(f"Total Academic Cheating Samples: {len(academic_samples)}")

    # Heuristics for Potential False Positives (Legitimate Inquiries? / Other Cats)
    
    # 1. Commercial Indicators (Strong Cheating)
    commercial_kws = ['سعر', 'ريال', 'تواصل', 'خاص', 'خدمات', 'متوفر', 'انجاز', 'دفع', 'تحويل', 'فلوس', 'مقابل']
    
    # 2. Legitimate-sounding Indicators (Potential Normal)
    # Asking for explanation, time, location, generic help without mentioning money/solution-for-hire directly
    legit_kws = ['شرح', 'كيف', 'متى', 'وين', 'طريقة', 'استفسار', 'مساعدة', 'لوجه الله']
    
    potential_mislabel = []
    medical_leak = []

    for i, sample in enumerate(academic_samples):
        text = sample['text']
        
        # Check for Medical Leak (keywords that might have been missed)
        if any(kw in text for kw in ['سكليف', 'اجازة', 'طبي', 'صحتي', 'مرضية']):
            medical_leak.append({'text': text[:60], 'id': i})
            continue

        # Check for Non-Commercial "Questions" (Potential Normal)
        # Condition: Has Question mark OR Legit KW, AND NO Commercial KW
        has_commercial = any(kw in text for kw in commercial_kws)
        has_legit = any(kw in text for kw in legit_kws)
        is_question = '?' in text
        
        if (has_legit or is_question) and not has_commercial:
            # High risk of being Normal (just asking for help/info)
            # Exclude strict cheating phrases like "حل واجب" if they appear alone? 
            # Actually "حل واجب" is usually cheating. But "كيف حل واجب" is normal.
            
            # If text says "ابي احد يحل لي" (I want someone to solve for me) -> Cheating
            # If text says "كيف احل" (How do I solve) -> Normal
            
            if re.search(r'كيف\s.*(احل|حل)', text):
                 potential_mislabel.append({'text': text[:60], 'id': i, 'reason': 'Question about "How to"'})
            elif not re.search(r'(يحل|حل\s*لي|ابي\s*حل)', text):
                 potential_mislabel.append({'text': text[:60], 'id': i, 'reason': 'General inquiry without clear cheating intent'})

    print(f"\n⚠️ Potential Medical Leaks: {len(medical_leak)}")
    for m in medical_leak:
        print(f"   - {m['text']}...")

    print(f"\n⚠️ Potential False Positives (Normal?): {len(potential_mislabel)}")
    print("   (These might be students asking for help/explanation, not cheating services)")
    for m in potential_mislabel[:20]:
        print(f"   - [{m['reason']}] {m['text']}...")

if __name__ == "__main__":
    main()
