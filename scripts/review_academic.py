
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🎓 Reviewing 'Academic Cheating' Category...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Regex for Requests (Strong indicators)
    # Use word boundaries for short words!
    re_req_strong = re.compile(r'(مين (يحل|عنده|يسوي|يعرف)|ابغى|ابي|احتاج|محتاج|بغيت|هل (فيه|يوجد|احد)|ممكن (احد|مساعدة)|بحث عن|لوسمحتوا|تكفون|احد يخبر|ضروري|كم السعر|\bبكم\b)', re.DOTALL)
    
    # Regex for "Who Needs" (Specific Offer pattern)
    re_who_needs = re.compile(r'(اللي|الي|مين|من) (محتاج|يبي|يشتي|يبغى|بحاجة)', re.DOTALL)
    
    # Regex for Offers (Strong indicators)
    # "Contact me", "Available", "Discount", "We do", "My number", "Services"
    re_off_strong = re.compile(r'(تواصل (معنا|معي|واتس)|رقمي|05\d+|966\d+|خصم|عرض|عروض|لدينا|نقدم|متوفر|متاح|انجاز|فوري|الدفع بعد|مكتب|خدمات|حياكم|الرابط|شعارنا|خبرة|سنوات)', re.DOTALL)

    move_count = 0
    
    for sample in data:
        labels = sample.get('labels', [])
        current_label = labels[0] if labels else 'Normal'
        
        if 'Academic Cheating' in current_label:
            text = sample['text']
            
            # Improved Logic:
            # 1. "Who needs" ( اللي محتاج / من يبغى ) -> OFFER (if followed by contact info)
            # 2. "Who can" ( مين يحل / من يقدر ) -> REQUEST
            
            new_label = None
            is_req_pure = re_req_strong.search(text)
            is_off_pure = re_off_strong.search(text)
            
            # Contextual Checks
            # Offer Context (Strict)
            has_offer_context_strict = re.search(r'(حياكم|عرض|خصم|لدينا|نقدم|خدمات|مكتب|انجاز|فوري|أسعار|سعر|تحويل|دفع)', text)
            
            # 1. "Who needs" check
            is_who_needs = re_who_needs.search(text)
            
            has_request_context = re.search(r'(ابغى|ابي|احتاج|بغيت|هل يوجد|مين يعرف|ممكن احد|محتاج|بحث عن)', text)
            
            if current_label == 'Academic Cheating (Offer)':
                # Move to Request IF:
                # 1. Has Explicit Request Context
                # 2. AND does NOT have Commercial Context
                # 3. AND is NOT a "Who Needs" offer
                if has_request_context and not has_offer_context_strict and not is_who_needs:
                    new_label = 'Academic Cheating (Request)'
                elif ('\bبكم\b' in text or 'كم السعر' in text) and not has_offer_context_strict:
                     new_label = 'Academic Cheating (Request)'

            elif current_label == 'Academic Cheating (Request)':
                # Move BACK to Offer IF:
                # 1. Has Strong Commercial Context
                # 2. OR is "Who Needs" pattern
                if has_offer_context_strict or is_who_needs:
                     new_label = 'Academic Cheating (Offer)'
            
            if new_label and new_label != current_label:
                print(f"[{current_label} -> {new_label}] {text[:60]}...")
                sample['labels'] = [new_label]
                sample['label'] = new_label
                sample['note'] = f"Manual Review: {current_label} -> {new_label}"
                sample['reviewed_at'] = datetime.now().isoformat()
                move_count += 1
                
        # Also check 'Normal' samples? No, let's stick to refining the split first.

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Moved {move_count} samples from Offer to Request in Academic Cheating.")

if __name__ == "__main__":
    main()
