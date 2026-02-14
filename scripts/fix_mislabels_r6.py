"""
Fix Mislabeled Training Samples - Round 6 (Sixth Full Re-audit)
Final cleanup: religious content, bus numbers, GPA discussions, and cross-category fixes.
"""
import json
import os
import shutil
from datetime import datetime
from collections import Counter

DATA_PATH = "al_rased/data/labeledSamples/training_data.json"
BACKUP_DIR = "al_rased/data/labeledSamples/backups"

FIXES = [
    # ========================================================
    # MEDICAL FRAUD → NORMAL (not medical at all)
    # ========================================================
    (1476, "طبيعي", ["طبيعي"],
     "أرقام باصات نقل موسمي = ليست احتيال طبي بل معلومات نقل"),
    (1483, "طبيعي", ["طبيعي"],
     "لو طلع بالتطبيق 4.66 لما ينزل بأكاديميا يصير 4.64 = نقاش معدل GPA"),

    # ========================================================
    # HACKING → UNETHICAL (child exploitation content)
    # ========================================================
    (1484, "غير أخلاقي (عرض)", ["غير أخلاقي (عرض)"],
     "أفلام أطفال واغتصاب وتجسس = محتوى غير أخلاقي بالتأكيد وليس تهكير"),

    # ========================================================
    # UNETHICAL → NORMAL (prayer/دعاء)
    # ========================================================
    (1490, "طبيعي", ["طبيعي"],
     "أسأل الله الذي لا يعجزه شيء أن يعطيك = دعاء ديني بريء"),

    # ========================================================
    # UNETHICAL → SPAM (comedy group promotion)
    # ========================================================
    (1491, "سبام", ["سبام"],
     "ضايج وتريد تضحك تعال لربع الله تحشيش = ترويج قروب تليجرام"),

    # ========================================================
    # UNETHICAL → FINANCIAL SCAM (work from home scam)
    # ========================================================
    (1498, "احتيال مالي (عرض)", ["احتيال مالي (عرض)"],
     "مجال مره حلو تاخذ فلوس وانت قاعد في المنزل = احتيال مالي"),

    # ========================================================
    # SPAM → NORMAL (educational/religious content)
    # ========================================================
    (2022, "طبيعي", ["طبيعي"],
     "إرشادات منصة الدعم الموحد للبلاغات = معلومات إرشادية تعليمية"),
    (2045, "طبيعي", ["طبيعي"],
     "يا منزل الآيات والفرقان بيني وبينك حرمة القرآن = شعر ديني"),

    # ========================================================
    # FINANCIAL SCAMS → NORMAL (religious/general content)
    # ========================================================
    (2027, "طبيعي", ["طبيعي"],
     "قناعات رمضانية عن الطاعات والمعاصي = محتوى ديني"),

    # ========================================================
    # UNETHICAL → SPAM (Minecraft server)
    # ========================================================
    (2037, "سبام", ["سبام"],
     "تم افتتاح سيرفر Special Craft تيمات وفعاليات = إعلان سيرفر لعبة"),

    # ========================================================
    # FINANCIAL SCAMS → SPAM (business consultancy)
    # ========================================================
    (2041, "سبام", ["سبام"],
     "دراسة مشروعك علينا دراسة جدوى = خدمات استشارات أعمال"),
]


def main():
    print("=" * 60)
    print("🔧 إصلاح العينات - الجولة السادسة")
    print("=" * 60)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📊 إجمالي العينات: {len(data)}")

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"training_data_pre_fix_r6_{ts}.json")
    shutil.copy2(DATA_PATH, backup_path)
    print(f"💾 نسخة احتياطية: {backup_path}")

    print("\n📊 إحصائيات قبل:")
    before = Counter(d["label"] for d in data)
    for k, v in before.most_common():
        print(f"  {k}: {v}")

    print(f"\n🔧 تطبيق {len(FIXES)} إصلاح...")
    print("-" * 60)

    fix_count = 0
    skipped = 0
    for idx, new_label, new_labels, reason in FIXES:
        if idx >= len(data):
            continue
        sample = data[idx]
        old_label = sample.get("label", "")
        if old_label == new_label and sample.get("labels", []) == new_labels:
            skipped += 1
            continue

        sample["label"] = new_label
        sample["labels"] = new_labels
        sample["note"] = f"Fix R6: {old_label} -> {new_label} ({reason})"
        sample["reviewed_at"] = datetime.now().isoformat()
        sample["reviewed_by"] = "full_audit_r6_feb2026"

        fix_count += 1
        text_preview = sample["text"][:50].replace('\n', ' ')
        print(f"  ✅ [{idx}] {old_label} -> {new_label}")
        print(f"       {text_preview}...")

    if skipped:
        print(f"\n  ⏭️  تخطي {skipped}")

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n📊 إحصائيات بعد:")
    after = Counter(d["label"] for d in data)
    for k, v in after.most_common():
        diff = v - before.get(k, 0)
        marker = f" ({'+' if diff > 0 else ''}{diff})" if diff != 0 else ""
        print(f"  {k}: {v}{marker}")

    print(f"\n✅ تم إصلاح {fix_count} عينة")


if __name__ == "__main__":
    main()
