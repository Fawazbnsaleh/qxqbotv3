"""
Full Comprehensive Audit of ALL Training Samples (v2)
Reads every sample and checks for mislabels using keyword rules,
contextual analysis, and cross-category validation.
"""
import json
import re
from collections import Counter, defaultdict

DATA_PATH = "al_rased/data/labeledSamples/training_data.json"

# ===== KEYWORD PATTERNS FOR EACH CATEGORY =====

# Academic Cheating (Offer) - someone offering to solve homework
ACADEMIC_OFFER_PATTERNS = [
    re.compile(r"(احل|بحل|نحل|اسوي|بسوي|نسوي|اعمل|بعمل|نعمل).{0,20}(واجب|بحث|بحوث|مشروع|تقرير|تكليف|تكاليف|اختبار|كويز|امتحان|برزنتيشن|بوربوينت)", re.I),
    re.compile(r"(واجب|بحث|بحوث|مشروع|تقرير|تكاليف|اختبار|كويز|امتحان).{0,20}(فل مارك|فلمارك|مضمون|الدرجه|الدرجة)", re.I),
    re.compile(r"(خدمات|مساعد).{0,15}(طلاب|طالب|دراس|جامع|اكاديم)", re.I),
    re.compile(r"(حلول|حل).{0,15}(دراس|جامع|اكاديم)", re.I),
    re.compile(r"(معلم|مدرس|دكتور).{0,20}(يحل|تحل|حل|واجب|اختبار)", re.I),
    re.compile(r"(اللي|الي) يبي.{0,20}(حل|واجب|بحث|مشروع|تكاليف)", re.I),
    re.compile(r"(بحوث|مشاريع|واجبات).{0,15}(تخرج|جامع|دراس)", re.I),
    re.compile(r"خدمات.{0,10}(الكتروني|إلكتروني).{0,30}(حل|واجب|بحث|مشروع|تكاليف|تقرير)", re.I),
    re.compile(r"(نقدم|نقدّم).{0,30}(حل|واجب|بحث|مشروع|تكاليف|تقرير|دراس)", re.I),
]

# Academic Cheating (Request) - someone asking for help solving
ACADEMIC_REQUEST_PATTERNS = [
    re.compile(r"(من|منو|فيه احد|احد|هل فيه|تعرفون|يعرف).{0,15}(يحل|تحل|يسوي|تسوي|يساعد|تساعد).{0,15}(واجب|بحث|مشروع|تقرير|تكليف|اختبار|كويز)", re.I),
    re.compile(r"(ابي|ابغى|محتاج|يبي).{0,15}(احد|حد|شخص).{0,10}(يحل|يسوي|يساعد)", re.I),
    re.compile(r"(من يحل|من تحل|من يقدر يحل)", re.I),
    re.compile(r"(الي يحل|اللي يحل).{0,10}(يرسل|يتواصل|يكلم)", re.I),
]

# Medical Fraud - selling fake sick leaves / medical excuses
MEDICAL_FRAUD_PATTERNS = [
    re.compile(r"(سكليف|سڪليف|سكلف|شكليف|سكاليف|سكالف|سگليف)", re.I),
    re.compile(r"(عذر|اعذار|أعذار).{0,10}(طب|مرض)", re.I),
    re.compile(r"(اجازة|اجازه|إجازة|إجازه).{0,10}(مرض|طب)", re.I),
    re.compile(r"(صحتي|صحتى|منصة صحتي)", re.I),
    re.compile(r"(نطلع|اطلع|تسوي|نسوي|اسوي).{0,15}(اعذار|سكليف|سكلف)", re.I),
    re.compile(r"(غياب|تغيب).{0,20}(اعذار|عذر|سكليف|طب|مرض)", re.I),
]

# Financial Scams - investment fraud, get-rich-quick schemes
FINANCIAL_SCAM_PATTERNS = [
    re.compile(r"(استثمر|استثمار|invest).{0,15}(مع|معي|معنا|الان|الآن|فرص)", re.I),
    re.compile(r"(ارباح|أرباح|ربح|عوائد).{0,15}(مضمون|يومي|شهري|بدون)", re.I),
    re.compile(r"(فوركس|forex|تداول عملات|crypto|كريبتو)", re.I),
    re.compile(r"(دخل|ربح).{0,10}(اضافي|إضافي|من البيت|بدون مجهود)", re.I),
    re.compile(r"(فرصة|فرص).{0,10}(ذهبي|استثمار|ربح)", re.I),
    re.compile(r"(ETH|BTC|USDT|bitcoin|ethereum).{0,20}(giveaway|free|airdrop)", re.I),
]

# Spam - generic advertisements, promotions, group joins
SPAM_PATTERNS = [
    re.compile(r"(سيرفر|ريلم).{0,10}(ماينكرافت|ماين كرافت|كرافت|ديسكورد)", re.I),
    re.compile(r"(شحن|رشق).{0,10}(متابعين|لايكات|شدات|جواهر)", re.I),
    re.compile(r"(اشتراك|قسائم|كوبون|كوبونات|قسيمة)", re.I),
    re.compile(r"(متجر|ستور|shop).{0,15}(الكتروني|إلكتروني|اون لاين|online)", re.I),
    re.compile(r"(تقسيط|قسط).{0,15}(بطاق|جوال|ايفون|آيفون|سامسونج)", re.I),
    re.compile(r"(سجل|انضم|ادخل).{0,15}(رابط|لينك|قروب|قناة|link)", re.I),
]

# Hacking - hacking services
HACKING_PATTERNS = [
    re.compile(r"(تهكير|اختراق|هكر|هاكر|hack)", re.I),
    re.compile(r"(فك|فتح|استرجاع).{0,10}(حساب|حظر|باسورد|كلمة سر)", re.I),
    re.compile(r"(تجسس|مراقب).{0,10}(واتس|واتساب|هاتف|جوال|تلفون)", re.I),
    re.compile(r"(سحب|سرقة).{0,10}(بيانات|معلومات|حساب)", re.I),
]

# Unethical - sexual content, drugs, exploitation
UNETHICAL_PATTERNS = [
    re.compile(r"(سكس|sex|porn|xxx|نيك|بورن|نودز|nudes)", re.I),
    re.compile(r"(هيجان|هيجانه|شهوه|شهوة|نيكني|انيك)", re.I),
    re.compile(r"(فيديو كول|سكس شات|video call).{0,10}(بنات|حريم|نساء)", re.I),
    re.compile(r"(حشيش|شبو|كبتاجون|كريستال|مخدر|حبوب).{0,10}(للبيع|متوفر|متاح|عندي)", re.I),
    re.compile(r"(قاصر|اطفال).{0,10}(سكس|تحرش|جنس)", re.I),
]

# Normal indicators - things that suggest the text is actually normal conversation
NORMAL_INDICATORS = [
    re.compile(r"(نصابين|نصاب|محتالين|محتال).{0,20}(ذول|هؤلاء|هؤلا)", re.I),
    re.compile(r"(حذر|انتبه|تحذير|خلوا بالكم)", re.I),
    re.compile(r"(مافيه الا|حقين|حوموا كبدي|يرجال)", re.I),
    re.compile(r"(هل|متى|وش|ايش|كيف).{0,30}(الاختبار|امتحان|اعذار|عذر|تقديم)", re.I),
    re.compile(r"(سبق|احد|هل).{0,20}(اختبر|قدم|سجل|رفع).{0,15}(اعذار|عذر|تذكر)", re.I),
    re.compile(r"(خطوات|طريقة|كيف).{0,15}(رفع|تقديم).{0,10}(تذكر|عذر|طلب)", re.I),
    re.compile(r"(مشكلة|مشكله|مواجه|صعوبة|صعوبه).{0,15}(مشروع|واجب|تسجيل)", re.I),
    re.compile(r"(دام ان|ترا|بالنسبة|بخصوص).{0,20}(المشاري|البحث|الدراس)", re.I),
    re.compile(r"(واختبارات|اختباراتها|اختبارات).{0,10}(سهل|صعب|حلو|حلوه|ممتاز)", re.I),
    re.compile(r"(ابحث عن|ابي|ابغى).{0,10}(وظيف|عمل|شغل)", re.I),
    re.compile(r"(انا بتخرج|بعد التخرج|وش الاختبارات)", re.I),
    re.compile(r"(اشتري|ابيع).{0,10}(حساب|جهاز|لابتوب|جوال)", re.I),
]


def classify_text(text):
    """Return list of (category, confidence_reason) tuples that match the text."""
    matches = []
    
    # Check normal indicators first
    normal_match = False
    for p in NORMAL_INDICATORS:
        m = p.search(text)
        if m:
            normal_match = True
            matches.append(("طبيعي", f"normal indicator: {m.group()}"))
    
    for p in MEDICAL_FRAUD_PATTERNS:
        m = p.search(text)
        if m:
            matches.append(("احتيال طبي (عرض)", f"medical: {m.group()}"))
    
    for p in ACADEMIC_OFFER_PATTERNS:
        m = p.search(text)
        if m:
            matches.append(("غش أكاديمي (عرض)", f"acad_offer: {m.group()}"))
    
    for p in ACADEMIC_REQUEST_PATTERNS:
        m = p.search(text)
        if m:
            matches.append(("غش أكاديمي (طلب)", f"acad_request: {m.group()}"))
    
    for p in FINANCIAL_SCAM_PATTERNS:
        m = p.search(text)
        if m:
            matches.append(("احتيال مالي (عرض)", f"financial: {m.group()}"))
    
    for p in SPAM_PATTERNS:
        m = p.search(text)
        if m:
            matches.append(("سبام", f"spam: {m.group()}"))
    
    for p in HACKING_PATTERNS:
        m = p.search(text)
        if m:
            matches.append(("تهكير (عرض)", f"hacking: {m.group()}"))
    
    for p in UNETHICAL_PATTERNS:
        m = p.search(text)
        if m:
            matches.append(("غير أخلاقي (عرض)", f"unethical: {m.group()}"))
    
    return matches, normal_match


# Map English labels to Arabic broad categories for comparison
LABEL_FAMILY = {
    "Academic Cheating": "أكاديمي",
    "غش أكاديمي (عرض)": "أكاديمي",
    "غش أكاديمي (طلب)": "أكاديمي",
    "Medical Fraud": "طبي",
    "احتيال طبي (عرض)": "طبي",
    "احتيال طبي (طلب)": "طبي",
    "Financial Scams": "مالي",
    "احتيال مالي (عرض)": "مالي",
    "احتيال مالي (طلب)": "مالي",
    "Spam": "سبام",
    "سبام": "سبام",
    "Hacking": "تهكير",
    "تهكير (عرض)": "تهكير",
    "تهكير (طلب)": "تهكير",
    "Unethical": "غير أخلاقي",
    "غير أخلاقي (عرض)": "غير أخلاقي",
    "غير أخلاقي (طلب)": "غير أخلاقي",
    "Normal": "طبيعي",
    "طبيعي": "طبيعي",
}

DETECTED_FAMILY = {
    "غش أكاديمي (عرض)": "أكاديمي",
    "غش أكاديمي (طلب)": "أكاديمي",
    "احتيال طبي (عرض)": "طبي",
    "احتيال مالي (عرض)": "مالي",
    "سبام": "سبام",
    "تهكير (عرض)": "تهكير",
    "غير أخلاقي (عرض)": "غير أخلاقي",
    "طبيعي": "طبيعي",
}


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 70)
    print(f"🔍 Full Audit of ALL {len(data)} Samples")
    print("=" * 70)

    issues = []  # (index, issue_type, current_label, suggested_label, text, reason)
    
    for i, sample in enumerate(data):
        text = sample.get("text", "")
        label = sample.get("label", "")
        labels = sample.get("labels", [])
        label_family = LABEL_FAMILY.get(label, "unknown")
        
        detected, is_normal = classify_text(text)
        
        if not detected:
            # No patterns matched - if labeled as violation, might be wrong
            # but we can't be sure, so skip
            continue
        
        # Get detected categories (families)
        detected_families = set()
        detected_cats = set()
        for cat, reason in detected:
            detected_families.add(DETECTED_FAMILY.get(cat, cat))
            detected_cats.add(cat)
        
        # === ISSUE 1: Normal sample that matches violation patterns ===
        if label_family == "طبيعي":
            violation_cats = [c for c in detected_cats if c != "طبيعي"]
            if violation_cats and not is_normal:
                # Normal but matched violation pattern and no normal indicators
                reasons = [r for c, r in detected if c != "طبيعي"]
                issues.append((i, "NORMAL_BUT_VIOLATION", label, violation_cats[0],
                               text, "; ".join(reasons[:2])))
        
        # === ISSUE 2: Violation sample that only matches Normal indicators ===
        elif label_family != "طبيعي":
            if is_normal and len(detected_cats - {"طبيعي"}) == 0:
                reasons = [r for c, r in detected if c == "طبيعي"]
                issues.append((i, "VIOLATION_BUT_NORMAL", label, "طبيعي",
                               text, "; ".join(reasons[:2])))
            
            # === ISSUE 3: Wrong violation category ===
            elif label_family not in detected_families and "طبيعي" not in detected_families:
                # The detected category doesn't match the label family at all
                main_detected = [c for c in detected_cats if c != "طبيعي"]
                if main_detected:
                    reasons = [r for c, r in detected if c != "طبيعي"]
                    issues.append((i, "WRONG_CATEGORY", label, main_detected[0],
                                   text, "; ".join(reasons[:2])))
        
        # === ISSUE 4: Offer vs Request confusion (Academic only) ===
        if label in ["غش أكاديمي (عرض)", "Academic Cheating"]:
            if "غش أكاديمي (طلب)" in detected_cats and "غش أكاديمي (عرض)" not in detected_cats:
                reasons = [r for c, r in detected if c == "غش أكاديمي (طلب)"]
                issues.append((i, "OFFER_IS_REQUEST", label, "غش أكاديمي (طلب)",
                               text, "; ".join(reasons[:2])))
        
        # === ISSUE 5: Spam labeled but really Academic Cheating ===
        if label_family == "سبام" and "أكاديمي" in detected_families:
            reasons = [r for c, r in detected if DETECTED_FAMILY.get(c) == "أكاديمي"]
            issues.append((i, "SPAM_IS_ACADEMIC", label, "غش أكاديمي (عرض)",
                           text, "; ".join(reasons[:2])))
        
        # === ISSUE 6: Financial Scams labeled but really Spam ===
        if label_family == "مالي" and "سبام" in detected_families and "مالي" not in detected_families:
            reasons = [r for c, r in detected if DETECTED_FAMILY.get(c) == "سبام"]
            issues.append((i, "FINANCIAL_IS_SPAM", label, "سبام",
                           text, "; ".join(reasons[:2])))
        
        # === ISSUE 7: Academic labeled but primarily Medical ===
        if label_family == "أكاديمي" and "طبي" in detected_families:
            medical_reasons = [r for c, r in detected if DETECTED_FAMILY.get(c) == "طبي"]
            academic_reasons = [r for c, r in detected if DETECTED_FAMILY.get(c) == "أكاديمي"]
            # If medical patterns come first in text or are more prominent
            if len(medical_reasons) >= len(academic_reasons):
                issues.append((i, "ACADEMIC_IS_MEDICAL", label, "احتيال طبي (عرض)",
                               text, "; ".join(medical_reasons[:2])))

    # Deduplicate issues (same index can appear multiple times)
    seen = set()
    unique_issues = []
    for issue in issues:
        idx = issue[0]
        if idx not in seen:
            seen.add(idx)
            unique_issues.append(issue)

    # Sort by issue type
    unique_issues.sort(key=lambda x: (x[1], x[0]))

    # Print results
    print(f"\n🔎 Found {len(unique_issues)} potential issues:\n")
    
    by_type = defaultdict(list)
    for issue in unique_issues:
        by_type[issue[1]].append(issue)
    
    for issue_type, group in sorted(by_type.items()):
        type_names = {
            "NORMAL_BUT_VIOLATION": "🟡 طبيعي لكن يحتوي كلمات مخالفة",
            "VIOLATION_BUT_NORMAL": "🟢 مخالفة لكنها في الحقيقة طبيعي",
            "WRONG_CATEGORY": "🔴 فئة خاطئة",
            "OFFER_IS_REQUEST": "🔵 عرض لكنه في الحقيقة طلب",
            "SPAM_IS_ACADEMIC": "🟠 سبام لكنه غش أكاديمي",
            "FINANCIAL_IS_SPAM": "🟣 احتيال مالي لكنه سبام",
            "ACADEMIC_IS_MEDICAL": "🩺 أكاديمي لكنه احتيال طبي",
        }
        print(f"\n{'='*60}")
        print(f"{type_names.get(issue_type, issue_type)} ({len(group)} عينة)")
        print(f"{'='*60}")
        
        for idx, itype, curr_label, suggested, text, reason in group:
            print(f"\n  [{idx:4d}] {curr_label} → {suggested}")
            print(f"         السبب: {reason}")
            # Print full text, wrapped
            text_display = text.replace('\n', ' ↵ ')
            if len(text_display) > 120:
                print(f"         النص: {text_display[:120]}...")
            else:
                print(f"         النص: {text_display}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 ملخص: {len(unique_issues)} عينة تحتاج مراجعة")
    for itype, group in sorted(by_type.items()):
        type_short = {
            "NORMAL_BUT_VIOLATION": "طبيعي→مخالفة",
            "VIOLATION_BUT_NORMAL": "مخالفة→طبيعي",
            "WRONG_CATEGORY": "فئة خاطئة",
            "OFFER_IS_REQUEST": "عرض→طلب",
            "SPAM_IS_ACADEMIC": "سبام→أكاديمي",
            "FINANCIAL_IS_SPAM": "مالي→سبام",
            "ACADEMIC_IS_MEDICAL": "أكاديمي→طبي",
        }
        print(f"  {type_short.get(itype, itype)}: {len(group)}")

    # Output as JSON for further processing
    output = []
    for idx, itype, curr_label, suggested, text, reason in unique_issues:
        output.append({
            "index": idx,
            "issue_type": itype,
            "current_label": curr_label,
            "suggested_label": suggested,
            "reason": reason,
            "text_preview": text[:80]
        })
    
    with open("scripts/audit_report_v2.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 تقرير مفصل: scripts/audit_report_v2.json")


if __name__ == "__main__":
    main()
