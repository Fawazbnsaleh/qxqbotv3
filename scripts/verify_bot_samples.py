
import json
import os
import sys
import random

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from al_rased.features.detection.engine import DetectionEngine

def main():
    print("🤖 Verifying Model against Real Bot Samples...")
    
    # Load Model
    DetectionEngine.load_model()
    
    # Load Samples
    sample_file = 'data/telethonSamplesv2/group_2333525822.json'
    try:
        with open(sample_file, 'r') as f:
            data = json.load(f)
            messages = data.get('messages', [])
    except FileNotFoundError:
        print(f"File not found: {sample_file}")
        return

    print(f"Loaded {len(messages)} messages from {sample_file}")
    
    # Pick random 200 messages to test
    if not messages:
        print("No messages found.")
        return

    test_batch = random.sample(messages, min(200, len(messages)))
    
    results = {
        'total': 0,
        'violations': 0,
        'requests': 0,
        'normal': 0
    }
    
    print("\n--- Detection Preview (Using Thresholds) ---")
    
    # Import thresholds logic
    from al_rased.features.detection.handlers import get_thresholds
    THRESHOLDS = get_thresholds()
    
    for msg in test_batch:
        text = msg.get('text', '')
        if not text: continue
        
        pred = DetectionEngine.predict(text)
        label = pred['label']
        conf = pred['confidence']
        
        if label == 'طبيعي':
            results['normal'] += 1
            if 'تواصل' in text and conf > 0.8:
                 print(f"❓ [Possible Miss?] [{label}] ({conf:.2f}): {text[:60]}...")
            continue

        # Check Threshold
        threshold = THRESHOLDS.get(label, 0.50)
        
        if conf < threshold:
            # Ignored by bot -> Effectively Normal
            results['normal'] += 1
            # print(f"⚪️ [Ignored] [{label}] ({conf:.2f} < {threshold}): {text[:60]}...")
        else:
            # Violation
            results['total'] += 1
            
            if '(عرض)' in label:
                results['violations'] += 1
                emoji = "🔴"
            elif '(طلب)' in label:
                results['requests'] += 1
                emoji = "🟡"
            elif 'سبام' in label:
                results['violations'] += 1
                emoji = "🔴"
            else:
                 emoji = "🔴"
                 
            print(f"{emoji} [{label}] ({conf:.2f} >= {threshold}): {text[:60]}...")

    print("\n--- Summary ---")
    print(f"Total Tested: {len(test_batch)}")
    print(f"Violations (Actionable): {results['violations']}")
    print(f"Requests (Actionable): {results['requests']}")
    print(f"Normal/Ignored: {results['normal']}")

if __name__ == "__main__":
    main()
