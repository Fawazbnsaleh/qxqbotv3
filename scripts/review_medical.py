
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("⚕️ Reviewing 'Medical Fraud' Category...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Request Indicators (Questions only)
    # "How to", "Method", "Can I", "Is it possible"
    re_questions = re.compile(r'(كيف (ارفع|انزل|اقدم)|طريقة (الرفع|التنزيل)|هل (نقدر|يمدينا|يطلع)|استفسار|سؤال|عندي (سكليف|اجازة))', re.DOTALL)
    
    # "I want" Indicators (Buying) - Rare but possible
    # "I need sick leave 2 days"
    re_want_buy = re.compile(r'(ابغى|احتاج|ابي|مطلوب).{0,20}(سكليف|اجازة|مرضية|عذر)', re.DOTALL)

    # Offer Indicators (Selling)
    re_offer = re.compile(r'(تواصل|واتس|مضمون|تنزل|توكلنا|صحتي|دفع|بعد الانجاز|فلوس|رسوم|تفريغ|مرافق)', re.DOTALL)

    move_count = 0
    
    for sample in data:
        labels = sample.get('labels', [])
        current_label = labels[0] if labels else 'Normal'
        
        if 'Medical Fraud' in current_label:
            text = sample['text']
            
            is_question = re_questions.search(text)
            is_want = re_want_buy.search(text)
            is_offer = re_offer.search(text)
            
            new_label = None
            
            if current_label == 'Medical Fraud (Offer)':
                # Move to Request IF:
                # 1. Is a Question ("How to") -> Request (or Normal? Let's say Request if it's about Fraud/Excuses)
                # 2. Is "I want" AND NO Offer specific keywords ("Guaranteed", "Payment")
                
                if is_question and not is_offer:
                     new_label = 'Medical Fraud (Request)'
                elif is_want and not is_offer:
                     new_label = 'Medical Fraud (Request)'
            
            # Note: "How to upload sick leave" is technically NOT Fraud, it might be Normal.
            # But if labeled Medical Fraud, we split to Request. 
            # Later we can decide if Medical Fraud (Request) == Normal. 
            # For now, let's just split.

            if new_label and new_label != current_label:
                print(f"[{current_label} -> {new_label}] {text[:60]}...")
                sample['labels'] = [new_label]
                sample['label'] = new_label
                sample['note'] = f"Manual Review: {current_label} -> {new_label}"
                sample['reviewed_at'] = datetime.now().isoformat()
                move_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Moved {move_count} samples from Offer to Request in Medical Fraud.")

if __name__ == "__main__":
    main()
