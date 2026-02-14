
import json
import re
import os
import sys

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("📊 Schema Migration Feasibility Analysis (Request vs Offer)...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # Heuristics
    # Request = Asking for something (Need, Want, Who can, Help)
    # Offer = Providing something (Available, We have, Contact me, Price, Discount)
    
    re_request = re.compile(r'(ابغى|مين عنده|مطلوب|احتاج|بغيت|ابي|هل يوجد|ممكن|شخص|يساعدني|استفسار|بحث عن|اريد)', re.DOTALL)
    re_offer = re.compile(r'(متوفر|يوجد|لدينا|حياكم|عروض|خصم|تواصل|واتس|خاص|نقدم|خدمات|لحل|سعر|اشترك|للبيع|حسابات)', re.DOTALL)

    categories = set()
    for d in data:
        labels = d.get('labels', [d.get('label', 'Normal')])
        for l in labels:
            categories.add(l)

    print(f"\nScanning {len(data)} samples across {len(categories)} categories...")

    results = {}

    for cat in categories:
        if cat == 'Normal': continue
        
        results[cat] = {'Request': 0, 'Offer': 0, 'Ambiguous': 0}
        
        cat_samples = [d for d in data if cat in d.get('labels', [d.get('label')])]
        
        for sample in cat_samples:
            text = sample['text']
            is_req = re_request.search(text)
            is_off = re_offer.search(text)
            
            if is_req and not is_off:
                results[cat]['Request'] += 1
            elif is_off and not is_req:
                results[cat]['Offer'] += 1
            elif is_off and is_req:
                # Conflict: Usually Offer wins if price/contact is involved
                # "I need someone to solve, contact me" -> Request
                # "Who needs solution? Contact me" -> Offer
                # Lets count as Ambiguous for now
                results[cat]['Ambiguous'] += 1
            else:
                results[cat]['Ambiguous'] += 1

    print("\n--- Estimated Distribution ---")
    print(f"{'Category':<20} | {'Request':<10} | {'Offer':<10} | {'Ambiguous':<10}")
    print("-" * 60)
    
    for cat, counts in results.items():
        print(f"{cat:<20} | {counts['Request']:<10} | {counts['Offer']:<10} | {counts['Ambiguous']:<10}")

if __name__ == "__main__":
    main()
