
import json
import re
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("🕵️ Reviewing 'Normal' Category for Hidden Violations/Requests...")
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    # 1. Academic Cheating
    # Offer: Commercial terms + Service terms
    re_aca_offer = re.compile(r'(حل|واجب|اختبار|تواصل|واتس|خصم|عرض|لدينا|خدمات|فوري|انجاز|سعر).{0,50}(خاص|ريال|دفع|تحويل|مضمون)', re.DOTALL)
    # Request: "Who can", "I need", "Start with Who/I"
    re_aca_req = re.compile(r'(مين (يحل|عنده|يسوي)|ابغى|ابي|احتاج|بغيت|هل (فيه|يوجد)|ممكن (احد|مساعدة)).{0,50}(واجب|اختبار|بحث|تخرج|مشروع)', re.DOTALL)

    # 2. Medical Fraud
    # Offer: "Sick leave" + "Guaranteed/Upload"
    re_med_offer = re.compile(r'(سكليف|مرضية|اجازة|عذر).{0,50}(مضمون|تنزل|صحتي|توكلنا|فلوس|بدون حضور)', re.DOTALL)
    # Request: "How to", "Where"
    re_med_req = re.compile(r'(كيف (ارفع|انزل)|وين (اقدم|القى)|هل (يقبلون)|عندي (سكليف|اجازة))', re.DOTALL)

    # 3. Financial Scams (Offer only usually)
    re_fin_offer = re.compile(r'(ربح|استثمار|تداول|دولار|يومي|أسبوعي).{0,50}(مضمون|رابط|سجل|واتس)', re.DOTALL)

    # 4. Spam
    re_spam = re.compile(r'(قروب|سيرفر|لايك|متابعة|دعم|تفسير احلام|روحاني)', re.DOTALL)

    # Safety Excludes (Keep as Normal)
    re_exclude = re.compile(r'(مجانا|تطوع|بدون مقابل|لوجه الله|نصيحة|تحذير|انتبهوا)', re.DOTALL)

    move_count = 0
    
    for sample in data:
        labels = sample.get('labels', [])
        current_label = labels[0] if labels else 'Normal'
        
        # Check Normal for missed violations
        # AND Check Academic Cheating for False Positives (from previous runs)
        if current_label == 'Normal' or 'Academic Cheating' in current_label:
            text = sample['text']
            new_label = None

            # RESCUE LEGITIMATE REQUESTS (Priority 1)
            # "Add subject", "Problem help me", "Schedule" -> Force back to Normal
            if re.search(r'(اضافة|حذف|تعديل|جدول|مشكلة|مساعدة|استفسار).{0,30}(مادة|شعبة|نظام|بوابة|مكافأة)', text):
                 if current_label != 'Normal':
                     new_label = 'Normal'
            
            # Check for Hacking specifically (WhatsApp unban etc)
            elif 'فك حظر' in text or 'استرجاع' in text:
                 new_label = 'Hacking (Offer)'

            # Check for Spam specifically (Furniture, nonsensical offers)
            elif 'محل مفروشات' in text or 'تابي' in text:
                 new_label = 'Spam'

            # Check for legitimate student requests (SAFEGUARD)
            # "Add subject", "Problem help me", "Schedule" -> Keep Normal
            elif re.search(r'(اضافة|حذف|جدول|مشكلة|مساعدة|استفسار).{0,30}(مادة|شعبة|نظام|بوابة)', text):
                 continue 

            elif re_med_offer.search(text):
                new_label = 'Medical Fraud (Offer)'
            elif re_aca_offer.search(text):
                new_label = 'Academic Cheating (Offer)'
            elif re_fin_offer.search(text):
                new_label = 'Financial Scams (Offer)'
            elif re_spam.search(text):
                new_label = 'Spam'
            
            # Check for Hidden Requests (Secondary)
            elif re_med_req.search(text):
                new_label = 'Medical Fraud (Request)'
            elif re_aca_req.search(text):
                new_label = 'Academic Cheating (Request)'

            if new_label:
                print(f"[Normal -> {new_label}] {text[:60]}...")
                sample['labels'] = [new_label]
                sample['label'] = new_label
                sample['note'] = f"Manual Review: Normal -> {new_label}"
                sample['reviewed_at'] = datetime.now().isoformat()
                move_count += 1

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Moved {move_count} samples from Normal to Correct Categories.")

if __name__ == "__main__":
    main()
