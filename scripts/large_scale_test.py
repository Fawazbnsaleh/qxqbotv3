"""
Large Scale Testing - Full Telethon Dataset.
Tests the model on ALL available messages and provides comprehensive statistics.
"""
import sys
import os
import json
import glob
from collections import Counter, defaultdict

sys.path.append(os.path.join(os.getcwd(), 'al_rased'))
from core.utils.text import normalize_text
from features.detection.engine import DetectionEngine

SOURCE_DIRS = [
    "/Users/apple/qxqbotv3/data/telethonSamples",
    "/Users/apple/qxqbotv3/data/telethonSamplesv2"
]

# Load thresholds
THRESHOLDS_FILE = "al_rased/features/detection/thresholds.json"
try:
    with open(THRESHOLDS_FILE, 'r') as f:
        THRESHOLDS = json.load(f)
except:
    THRESHOLDS = {"Medical Fraud": 0.42, "Academic Cheating": 0.39, "Financial Scams": 0.37, "Hacking": 0.34, "Spam": 0.34}

def load_all_messages():
    """Load ALL messages from both Telethon directories."""
    messages = []
    seen = set()
    file_count = 0
    
    for s_dir in SOURCE_DIRS:
        files = glob.glob(os.path.join(s_dir, "*.json"))
        for fpath in files:
            if "_metadata.json" in fpath:
                continue
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    msgs = data if isinstance(data, list) else data.get('messages', [])
                    for m in msgs:
                        txt = m.get('message') or m.get('text')
                        if txt and 10 < len(txt) < 1000 and txt not in seen:
                            messages.append(txt)
                            seen.add(txt)
                    file_count += 1
            except:
                pass
    
    print(f"Loaded {len(messages)} unique messages from {file_count} files")
    return messages

def run_large_scale_test():
    print("=" * 70)
    print("LARGE SCALE TEST - FULL TELETHON DATASET")
    print("=" * 70)
    
    # Load all messages
    messages = load_all_messages()
    total = len(messages)
    
    print(f"\nTesting on {total:,} messages...")
    print("-" * 70)
    
    # Statistics
    stats = {
        "total": total,
        "violations": 0,
        "normal": 0,
        "by_category": Counter(),
        "confidence_sum": defaultdict(float),
        "high_confidence": [],  # > 70%
        "low_confidence_violations": [],  # 30-50%
    }
    
    # Batch processing
    batch_size = 5000
    for i in range(0, total, batch_size):
        batch = messages[i:i+batch_size]
        progress = min(i + batch_size, total)
        print(f"  Processing {progress:,}/{total:,} ({100*progress/total:.1f}%)...", end='\r')
        
        for text in batch:
            result = DetectionEngine.predict(text)
            label = result["label"]
            confidence = result["confidence"]
            
            # Apply threshold
            threshold = THRESHOLDS.get(label, 0.40)
            
            if label != "Normal" and confidence >= threshold:
                stats["violations"] += 1
                stats["by_category"][label] += 1
                stats["confidence_sum"][label] += confidence
                
                if confidence >= 0.70:
                    stats["high_confidence"].append({
                        "text": text[:100],
                        "label": label,
                        "confidence": confidence
                    })
                elif confidence < 0.50:
                    stats["low_confidence_violations"].append({
                        "text": text[:100],
                        "label": label,
                        "confidence": confidence
                    })
            else:
                stats["normal"] += 1
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    # Summary
    violation_rate = 100 * stats["violations"] / total
    print(f"\nTotal Messages Tested: {total:,}")
    print(f"Violations Detected: {stats['violations']:,} ({violation_rate:.2f}%)")
    print(f"Normal Messages: {stats['normal']:,} ({100-violation_rate:.2f}%)")
    
    # By Category
    print("\n--- Detection by Category ---")
    for cat, count in stats["by_category"].most_common():
        avg_conf = stats["confidence_sum"][cat] / count if count > 0 else 0
        print(f"  {cat}: {count:,} detections, Avg Confidence: {avg_conf:.1%}")
    
    # High Confidence Samples
    print("\n--- Top 10 High Confidence Detections (>70%) ---")
    for item in sorted(stats["high_confidence"], key=lambda x: -x["confidence"])[:10]:
        print(f"  [{item['label']} - {item['confidence']:.0%}] {item['text'][:60]}...")
    
    # Low Confidence Violations
    print(f"\n--- Low Confidence Violations (30-50%): {len(stats['low_confidence_violations'])} total ---")
    for item in stats["low_confidence_violations"][:5]:
        print(f"  [{item['label']} - {item['confidence']:.0%}] {item['text'][:60]}...")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    return stats

if __name__ == "__main__":
    run_large_scale_test()
