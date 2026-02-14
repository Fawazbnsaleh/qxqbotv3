"""
Fix Mislabeled Training Samples
Corrects ~21 samples identified through comprehensive audit.
Creates a backup before applying changes.
"""
import json
import os
import shutil
from datetime import datetime
from collections import Counter

DATA_PATH = "al_rased/data/labeledSamples/training_data.json"
BACKUP_DIR = "al_rased/data/labeledSamples/backups"

# Each fix: (index, new_label, new_labels, reason)
FIXES = [
    # === Category 1: Labeled as Academic Cheating but should be Normal (discussing, not offering) ===
    (22, "طبيعي", ["طبيعي"], "يتحدث عن النصابين، ليس عرض غش"),
    (25, "طبيعي", ["طبيعي"], "يتحدث عن دكتوره تحل واجبات، مجرد إشارة"),
    (64, "طبيعي", ["طبيعي"], "شكوى من إعلانات حل واجبات في القروب"),
    (87, "طبيعي", ["طبيعي"], "مجرد إشارة بسيطة ليست عرض"),

    # === Category 2: Labeled as Spam but should be Academic Cheating ===
    (149, "غش أكاديمي (عرض)", ["غش أكاديمي (عرض)"], "إعلان تدريس خصوصي وحل واجبات"),
    (180, "غش أكاديمي (عرض)", ["غش أكاديمي (عرض)"], "خدمات حلول دراسية عن بعد"),
    (249, "غش أكاديمي (عرض)", ["غش أكاديمي (عرض)"], "دكتوره تسوي مشاريع وتحل امتحانات"),
    (444, "غش أكاديمي (عرض)", ["غش أكاديمي (عرض)"], "مؤسسة أبحاث أكاديمية"),
    (996, "غش أكاديمي (عرض)", ["غش أكاديمي (عرض)"], "إعلان مدرسة خصوصية تفاضل وتكامل"),

    # === Category 3: Spam but should be Normal ===
    (57, "طبيعي", ["طبيعي"], "باحث عن وظيفة، ليس سبام"),
    (148, "طبيعي", ["طبيعي"], "شكوى من البوت والمستجدين، ليس سبام"),

    # === Category 4: Academic Cheating but should be Medical Fraud ===
    (443, "احتيال طبي (عرض)", ["احتيال طبي (عرض)", "غش أكاديمي (عرض)"],
     "أعذار طبية هي العنصر الرئيسي"),
    (468, "احتيال طبي (عرض)", ["احتيال طبي (عرض)", "غش أكاديمي (عرض)"],
     "أعذار طبية هي العنصر الرئيسي - مكرر من 443"),
    (470, "احتيال طبي (عرض)", ["احتيال طبي (عرض)", "غش أكاديمي (عرض)"],
     "أعذار طبية من صحتي هي العنصر الرئيسي"),

    # === Category 5: Financial Scams -> Spam or Academic ===
    (536, "سبام", ["سبام"], "تقسيط بطاقات تجاري مشبوه، ليس احتيال مالي"),
    (581, "سبام", ["سبام"], "تسويق تطبيق جازي، ليس احتيال"),
    (936, "سبام", ["سبام"], "إعلان خدمات تطوير مواقع"),
    (992, "سبام", ["سبام"], "إعلان تجاري لشركة ألعاب"),
    (2011, "غش أكاديمي (عرض)", ["غش أكاديمي (عرض)"],
     "المساعدة في إعداد رسالة ماجستير ودكتوراه"),

    # === Category 6: Offer -> Request ===
    (128, "غش أكاديمي (طلب)", ["غش أكاديمي (طلب)"], "من يحل واجبات = طلب"),
    (138, "غش أكاديمي (طلب)", ["غش أكاديمي (طلب)"], "من يحل واجب = طلب"),
    (141, "غش أكاديمي (طلب)", ["غش أكاديمي (طلب)"], "تعرفون احد يحل = طلب"),
]


def main():
    print("=" * 60)
    print("🔧 إصلاح العينات الموسومة بالغلط")
    print("=" * 60)

    # Load data
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📊 إجمالي العينات: {len(data)}")

    # Create backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"training_data_pre_fix_{ts}.json")
    shutil.copy2(DATA_PATH, backup_path)
    print(f"💾 نسخة احتياطية: {backup_path}")

    # Show before stats
    print("\n📊 إحصائيات قبل الإصلاح:")
    before = Counter(d["label"] for d in data)
    for k, v in before.most_common():
        print(f"  {k}: {v}")

    # Apply fixes
    print(f"\n🔧 تطبيق {len(FIXES)} إصلاح...")
    print("-" * 60)

    fix_count = 0
    for idx, new_label, new_labels, reason in FIXES:
        if idx >= len(data):
            print(f"  ⚠️  [{idx}] خارج النطاق (max={len(data)-1})")
            continue

        sample = data[idx]
        old_label = sample.get("label", "")
        old_labels = sample.get("labels", [])
        text_preview = sample["text"][:50]

        if old_label == new_label and old_labels == new_labels:
            print(f"  ⏭️  [{idx}] بالفعل صحيح: {old_label}")
            continue

        # Apply fix
        sample["label"] = new_label
        sample["labels"] = new_labels
        sample["note"] = f"Mislabel Fix: {old_label} -> {new_label} ({reason})"
        sample["reviewed_at"] = datetime.now().isoformat()
        sample["reviewed_by"] = "mislabel_audit_feb2026"

        fix_count += 1
        print(f"  ✅ [{idx}] {old_label} -> {new_label}")
        print(f"       النص: {text_preview}...")
        print(f"       السبب: {reason}")

    # Save
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Show after stats
    print(f"\n📊 إحصائيات بعد الإصلاح:")
    after = Counter(d["label"] for d in data)
    for k, v in after.most_common():
        diff = v - before.get(k, 0)
        marker = f" ({'+' if diff > 0 else ''}{diff})" if diff != 0 else ""
        print(f"  {k}: {v}{marker}")

    print(f"\n✅ تم إصلاح {fix_count} عينة بنجاح.")
    print(f"💾 النسخة الاحتياطية محفوظة في: {backup_path}")


if __name__ == "__main__":
    main()
