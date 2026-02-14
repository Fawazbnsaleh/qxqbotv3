
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔧 Fixing 'Normal' Mislabels (Trusting Model logic)...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    fixed_count = 0
    
    # Heuristics derived from the Model's "False Positives" which are actually True Positives
    academic_services = [
        'اعداد رسائل', 'الماجستير', 'الدكتوراه', 'بربوزال', 
        'يحل واجبات', 'حل واجبات', 'عمل بحوث', 'خدمات طلابيه', 
        'مختص يساعدكم', 'تكاليف وعمل', 'شرح المواد', 'مكتب الدكتورة'
    ]
    
    for sample in data:
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        if 'Normal' not in labels:
            continue
            
        text = sample['text']
        
        # 1. Academic Services disguised as Normal
        if any(kw in text for kw in academic_services):
            # Double check: ensure it has commercial intent or service offer
            if any(kw in text for kw in ['تواصل', 'خاص', 'رقم', 'دكتورة', 'مكتب', 'سعر', 'نسوي', 'نقوم']):
                sample['labels'] = ['Academic Cheating']
                sample['label'] = 'Academic Cheating'
                sample['note'] = f"Auto-Fix: Normal -> Academic Cheating (Model Verification)"
                sample['reviewed_at'] = datetime.now().isoformat()
                fixed_count += 1
                
        # 2. Financial Scams (e.g. "investment")
        if 'استثمار' in text and 'ربح' in text:
             sample['labels'] = ['Financial Scams']
             sample['label'] = 'Financial Scams'
             sample['note'] = f"Auto-Fix: Normal -> Financial Scams (Model Verification)"
             sample['reviewed_at'] = datetime.now().isoformat()
             fixed_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Fixed {fixed_count} Mislabeled Normal samples.")

if __name__ == "__main__":
    main()
