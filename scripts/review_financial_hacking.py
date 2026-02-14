
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("💰/💻 Reviewing 'Financial' & 'Hacking' Categories...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Financial Requests: "Inquiries about investment", "Is this real"
    re_fin_req = re.compile(r'(هل (حقيقي|نصدق|مضمون)|كيف (استثمر|اربح)|وش رايكم|نصيحة|محتار|تنصحوني)', re.DOTALL)
    
    # Hacking Requests: "I need hacker", "Who can hack"
    re_hack_req = re.compile(r'(ابغى|احتاج|ابي|مين (يقدر|يعرف)|هكر|تهكير).{0,30}(انستا|سناب|حساب|واتس|استرجاع)', re.DOTALL)
    
    # Explicit Offer Keywords (to prevent moving actual offers)
    re_offer_strong = re.compile(r'(تواصل|واتس|رقم|لدينا|نقدم|خدمات|استرجاع|فوري|ثقة|ضمان)', re.DOTALL)

    move_count = 0
    
    for sample in data:
        labels = sample.get('labels', [])
        current_label = labels[0] if labels else 'Normal'
        text = sample['text']
        new_label = None
        
        if current_label == 'Financial Scams (Offer)':
            # Move to Request IF:
            # 1. Is Question/Advice seeking
            # 2. AND NOT an offer
            if re_fin_req.search(text) and not re_offer_strong.search(text):
                new_label = 'Financial Scams (Request)'

        elif current_label == 'Hacking (Offer)':
            # Move to Request IF:
            # 1. "I need hacker"
            # 2. AND NOT "We provide"
            if re_hack_req.search(text) and not re_offer_strong.search(text):
                new_label = 'Hacking (Request)'

        if new_label and new_label != current_label:
            print(f"[{current_label} -> {new_label}] {text[:60]}...")
            sample['labels'] = [new_label]
            sample['label'] = new_label
            sample['note'] = f"Manual Review: {current_label} -> {new_label}"
            sample['reviewed_at'] = datetime.now().isoformat()
            move_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Moved {move_count} samples from Offer to Request in Financial/Hacking.")

if __name__ == "__main__":
    main()
