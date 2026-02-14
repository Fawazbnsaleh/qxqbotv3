
import json
import re
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🕵️ Running Final Audit on Arabic Dataset...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Offer Keywords (Should NOT be in Request)
    re_offer_keywords = re.compile(r'(تواصل|واتس|رقم|لدينا|نقدم|خدمات|سعر|خصم|عرض|فوري|انجاز|تحويل|دفع|مضمون)', re.DOTALL)
    
    # Request Keywords (Should NOT be in Offer generally, but less strict)
    re_request_keywords = re.compile(r'(ابغى|ابي|احتاج|مين (يحل|يعرف|يسوي)|هل (يوجد|فيه)|ممكن (احد|مساعدة))', re.DOTALL)

    errors = 0
    fixed = 0
    
    for sample in data:
        labels = sample.get('labels', [])
        current_label = labels[0] if labels else 'طبيعي'
        text = sample['text']
        
        new_label = None

        # Rule 1: "Request" label BUT contains strong "Offer" keywords -> Move to Offer
        if '(طلب)' in current_label:
            if re_offer_keywords.search(text):
                # Check context - sometimes "Please contact me if you can help" is a request.
                # But usually "We provide... contact us" is offer.
                # Let's be strict: if it has "Discount", "Price", "We provide" -> Offer
                if re.search(r'(خصم|لدينا|نقدم|عرض|سعر|انجاز|فوري)', text):
                    base = current_label.replace('(طلب)', '(عرض)')
                    new_label = base
        
        # Rule 2: "Normal" containing obvious Offer keywords (Cleanup missed items)
        elif current_label == 'طبيعي':
             if re.search(r'(حل واجبات|بحوث|مشاريع|سكليف|مرضية).{0,50}(تواصل|واتس|مضمون)', text):
                 if 'سكليف' in text or 'مرضية' in text:
                     new_label = 'احتيال طبي (عرض)'
                 else:
                     new_label = 'غش أكاديمي (عرض)'

        if new_label:
            print(f"⚠️ [Correction] {current_label} -> {new_label}")
            print(f"   Text: {text[:60]}...")
            sample['labels'] = [new_label]
            sample['label'] = new_label
            fixed += 1
            errors += 1

    if fixed > 0:
        with open(data_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Fixed {fixed} issues.")
    else:
        print("✅ Audit Passed. No conflicting labels found.")

if __name__ == "__main__":
    main()
