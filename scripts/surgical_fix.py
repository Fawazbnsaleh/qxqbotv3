
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🩺 Surgical Fix for Stubborn Mislabels...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    clean_count = 0
    
    # Compile regexes for efficiency
    
    # 1. Academic Cheating (Services Only)
    # Must have "Solution/Homework" AND "Contact/Price" indicators
    re_cheat_service = re.compile(r'(حل|يحل|واجب|اختبار|أسعار|دكتور|خصوصي|ملخصات).{0,50}(خاص|ريال|تواصل|واتس|ثقة|فلوس|تحويل|سعر)', re.DOTALL)
    # Exclude: "How to", "Asking for help without payment context"
    re_cheat_exclude = re.compile(r'(كيف|طريقة|شرح|ممكن|احد يعرف|مساعدة في|ابغى شخص يجيني خاص من اللي طلبو)', re.DOTALL) # Added specific exclude for the branch change user

    # 2. Medical Fraud (Fake Sick Leaves)
    # Must have "Sick Leave" AND "Guaranteed/Upload" indicators
    re_med_fraud = re.compile(r'(سكليف|مرضية|اجازة|عذر|طبي).{0,50}(مضمون|تنزل|صحتي|توكلنا|بدون حضور|ذراع|فلوس)', re.DOTALL)
    re_med_exclude = re.compile(r'(كيف|طريقة|ارفع|دكتورة|استفسار|غياب|ادارة|مشكلة)', re.DOTALL)

    # 3. Unethical (Sexual/Offensive)
    re_unethical = re.compile(r'(مشتهيه|لزب|اريحها|فحل|سكس|محارم|شواذ)', re.DOTALL)

    # 4. Financial Scams (Job/Crypto)
    re_financial = re.compile(r'(مرتب|أسبوعي|ربح|استثمار|تداول|LinkedIn|دولار).{0,50}(ثابت|مضمون|سجل|رابط)', re.DOTALL)
    re_fin_exclude = re.compile(r'(نحتاج|مطلوب|وظيفة|خبرة)', re.DOTALL) # Try to avoid legit job posts if simple

    # 5. Spam (Specific)
    re_spam = re.compile(r'(تفسير احلام|سيرفر|قروب واتس|مفسر|مشترك|دعم|لايك)', re.DOTALL)


    for sample in data:
        current_labels = sample.get('labels', [sample.get('label', 'Normal')])
        if 'Normal' not in current_labels:
            continue
            
        text = sample['text']
        new_label = None
        
        # Check Unethical first (Highest Priority/Risk)
        if re_unethical.search(text):
            new_label = 'Unethical'
            
        # Check Medical Fraud
        elif re_med_fraud.search(text) and not re_med_exclude.search(text):
            new_label = 'Medical Fraud'
            
        # Check Academic Cheating
        elif re_cheat_service.search(text) and not re_cheat_exclude.search(text):
            new_label = 'Academic Cheating'
            
        # Check Financial
        elif re_financial.search(text) and not re_fin_exclude.search(text):
            new_label = 'Financial Scams'
            
        # Check Spam
        elif re_spam.search(text):
            new_label = 'Spam'

        if new_label:
            print(f"[{new_label}] {text[:60]}...")
            sample['labels'] = [new_label]
            sample['label'] = new_label
            sample['note'] = f"Auto-Fix: Surgical Regex ({new_label})"
            sample['reviewed_at'] = datetime.now().isoformat()
            clean_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Surgically Fixed {clean_count} samples.")

if __name__ == "__main__":
    main()
