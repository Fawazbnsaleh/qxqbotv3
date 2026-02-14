
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🔧 Fixing 'Normal' Category Anomalies...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    fix_count = 0
    
    for sample in data:
        labels = sample.get('labels', [sample.get('label', 'Normal')])
        if 'Normal' not in labels:
            continue
            
        text = sample['text']
        new_label = None
        
        # 1. Phone Numbers + Service keywords -> Spam/Academic/Medical
        if re.search(r'(05\d{8}|5\d{8}|\+9665\d{8})', text):
            if any(kw in text for kw in ['تصميم', 'خدمات', 'بيع', 'كحل']):
                new_label = 'Spam'
            elif any(kw in text for kw in ['دراسات', 'بحوث']):
                new_label = 'Academic Cheating'

        # 2. Hacking Code/Roblox Scripts -> Spam/Hacking
        if 'loadstring(game:HttpGet' in text:
            new_label = 'Hacking' # Actually it's game hacking, usually categorized as Spam or Hacking. Let's say Spam to avoid confusion with real hacking? No, Hacking is fine.

        # 3. WhatsApp Group Links (if mostly empty text) -> Spam
        if 'chat.whatsapp.com' in text:
             if len(text) < 100 and not any(kw in text for kw in ['قروب', 'دفعة', 'كلية']):
                 new_label = 'Spam'

        # 4. Explicit Commercial -> Spam
        if 'اسعاري رمزية' in text or 'لطلب' in text:
            new_label = 'Spam'
            
        # Apply Fix
        if new_label:
            sample['labels'] = [new_label]
            sample['label'] = new_label
            sample['note'] = f"Auto-Fix: Normal Anomaly -> {new_label} (Found suspicious patterns)"
            sample['reviewed_at'] = datetime.now().isoformat()
            fix_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Fixed {fix_count} suspicious Normal samples.")

if __name__ == "__main__":
    main()
