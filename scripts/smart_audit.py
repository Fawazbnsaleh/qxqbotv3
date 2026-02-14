
import json
import re
import os
import sys
from datetime import datetime
from collections import Counter

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from al_rased.features.detection.engine import DetectionEngine
from al_rased.features.detection.handlers import get_thresholds

# Expert Rules (Regex Patterns)
EXPERT_RULES = {
    'Academic Cheating': [
        r'حل\s*واجب', r'حل\s*اختبار', r'مشاريع\s*تخرج', r'رسائ?ل\s*ماجستير', 
        r'اعداد\s*بحوث', r'خدمات\s*طلابية', r'اسايمنت', r'كويزات', r'تسميع',
        r'حلول\s*واجبات', r'مساعدة\s*في\s*الاختبار', r'قروب\s*حل', r'أبحاث\s*جامعية'
    ],
    'Medical Fraud': [
        r'سكليف', r'اجازة\s*مرضية', r'تقرير\s*طبي', r'عذر\s*طبي', r'مشهد\s*مرافقة',
        r'مستشفى\s*حكومي', r'منصة\s*صحتي', r'تطبيق\s*صحتي', r'مرضيه\s*معتمده'
    ],
    'Financial Scams': [
        r'استثم[رار]', r'ارباح\s*مضمونة', r'تداول', r'فوركس', r'عملات\s*رقمية',
        r'ادارة\s*محافظ', r'ربح\s*يومي', r'دخل\s*اضافي', r'توصيات\s*ذهب'
    ],
    'Hacking': [
        r'تهكير', r'اختراق', r'تجسس', r'سحب\s*صور', r'استرداد\s*حساب',
        r'زيادة\s*متابعين', r'توثيق\s*حساب'
    ],
    'Unethical': [
        r'سكس', r'ني[كڪ]', r'ممحون', r'ديوث', r'قحبة', r'سهرات', r'مساج', r'مدلعة',
        r'حشيش', r'مخدرات', r'كبتاجون', r'شبو'
    ],
    'Spam': [
        r'سيرفر\s*ماينكرافت', r'تبادل\s*نشر', r'اشترك\s*في\s*قناتنا', r'زيادة\s*متابعين',
        r'ارقام\s*وهمية', r'تفعيل\s*تليجرام', r'رشق'
    ]
}

def check_expert_rules(text):
    text = text.lower()
    matches = []
    for label, patterns in EXPERT_RULES.items():
        for pattern in patterns:
            if re.search(pattern, text):
                matches.append({'label': label, 'pattern': pattern})
                break 
    return matches

def main():
    print("🔍 Starting Smart Audit...")
    
    # Load Data
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)
    print(f"📊 Loaded {len(data)} samples")

    # Load Model
    print("🤖 Loading Model...")
    DetectionEngine.load_model()
    thresholds = get_thresholds()

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = [f"# 🧐 Smart Audit Report - {current_time}\n"]

    mismatches = []
    weak_samples = []
    pattern_matches = []
    
    # Analyze
    for i, sample in enumerate(data):
        text = sample['text']
        current_labels = sample.get('labels', [sample.get('label', 'Normal')])
        if isinstance(current_labels, str): current_labels = [current_labels]
        
        # 1. Model Prediction Check
        pred = DetectionEngine.predict(text)
        pred_label = str(pred['label'])
        confidence = pred['confidence']
        threshold = thresholds.get(pred_label, 0.5)
        
        # 2. Expert Rules Check
        rules = check_expert_rules(text)
        rule_labels = [m['label'] for m in rules]
        
        # A. Label Validation (Critical Errors)
        # Case: Label says Normal/Other, but Expert Rule says VIOLATION
        for match in rules:
            if match['label'] not in current_labels:
                mismatches.append({
                    'id': i,
                    'text': text[:100],
                    'current': current_labels,
                    'suggested': match['label'],
                    'reason': f"Expert Rule: {match['pattern']}",
                    'confidence': confidence
                })

        # Case: Label is Violation, but text seems Normal (harder, check confidence)
        if 'Normal' not in current_labels and not rules and confidence < 0.6:
             # If no expert keyword found and model is low confidence, might be false positive
             weak_samples.append({
                'id': i,
                'text': text[:100],
                'current': current_labels,
                'reason': "Low confidence violation without expert keyword match",
                'confidence': confidence
             })

        # B. Weak Samples (Low Confidence / Notes)
        note = sample.get('note', '').lower()
        if 'weak' in note or 'false' in note or (confidence > threshold - 0.15 and confidence < threshold + 0.1):
             # Gray zone / flagged samples
             pass # Already covered by gray zone logic, but let's log if not duplicate

        # C. Pattern Detection (Suspicious Normal)
        if 'Normal' in current_labels:
            # Check for patterns that fool model
            # E.g., repeated content
            if len(text) > 100 and len(set(text)) < 20: # Spammy repetition
                pattern_matches.append({
                    'id': i,
                    'text': text[:100],
                    'type': "Repetitive Spam",
                    'current': "Normal"
                })
            # Emojis overload
            emoji_count = len(re.findall(r'[^\w\s,\.]', text))
            if emoji_count > 10 and len(text) < 200:
                pattern_matches.append({
                    'id': i,
                    'text': text[:100],
                    'type': "Emoji Spam",
                    'current': "Normal"
                })

    # Generate Report
    
    # 1. Mismatches (Critical)
    report.append("## 🚨 Critical Mismatches (Label vs Expert Rules)")
    report.append(f"Found **{len(mismatches)}** potential errors.\n")
    if mismatches:
        report.append("| Text Snippet | Current Label | Suggested Label | Reason |")
        report.append("|--------------|---------------|-----------------|--------|")
        for m in mismatches[:20]: # Limit output
            report.append(f"| {m['text'].replace('|', '')}... | {m['current']} | **{m['suggested']}** | {m['reason']} |")
    
    # 2. Weak Samples
    report.append("\n## ⚠️ Weak / Ambiguous Samples")
    report.append(f"Found **{len(weak_samples)}** weak violations.\n")
    if weak_samples:
        report.append("| Text Snippet | Current Label | Confidence | Reason |")
        report.append("|--------------|---------------|------------|--------|")
        for m in weak_samples[:10]:
            report.append(f"| {m['text'].replace('|', '')}... | {m['current']} | {m['confidence']:.2f} | {m['reason']} |")
            
    # 3. Suspicious Patterns
    report.append("\n## 🕵️ Suspicious Patterns in 'Normal'")
    report.append(f"Found **{len(pattern_matches)}** suspicious samples.\n")
    if pattern_matches:
        for m in pattern_matches[:5]:
            report.append(f"- **{m['type']}**: `{m['text']}...`")

    # 4. Note Field Improvement
    report.append("\n## 💡 Note Field Strategy")
    report.append("""
Current 'note' usage is sparse. Recommendation for Active Learning:
- Auto-populate 'note' when fixing samples (e.g., "Fixed: Keyword 'X' detected").
- Use structured tags in note: `#FalsePositive`, `#WeakSignal`, `#KeywordMismatch`.
- During review, if User changes label, prompt for reason and save to 'note'.
    """)
    
    # 5. Quality Score
    total_issues = len(mismatches) + len(weak_samples) + len(pattern_matches)
    quality_score = max(0, 100 - (total_issues / len(data) * 100 * 5)) # Penalty factor
    report.append(f"\n## 🏆 Dataset Quality Score: **{quality_score:.1f}/100**")
    report.append(f"- Total Samples: {len(data)}")
    report.append(f"- Total Issues Found: {total_issues}")

    # Write Report
    with open('smart_audit_report.md', 'w') as f:
        f.write('\n'.join(report))
    
    print(f"✅ Audit Complete. Report saved to smart_audit_report.md")
    print(f"Found {len(mismatches)} mismatches and {len(weak_samples)} weak samples.")

if __name__ == "__main__":
    main()
