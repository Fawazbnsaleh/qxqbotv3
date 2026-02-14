
import json
import os
import sys
from datetime import datetime

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from al_rased.features.detection.engine import DetectionEngine
from al_rased.core.utils.text import normalize_text

def main():
    print("🤖 Starting Model-Based Self-Correction...")
    
    # Load Engine
    DetectionEngine.load_model()
    model = DetectionEngine._model
    # Ensure Keywords are loaded too just in case
    DetectionEngine.load_model()
    
    data_path = 'al_rased/data/labeledSamples/training_data.json'
    with open(data_path, 'r') as f:
        data = json.load(f)

    fixed_count = 0
    
    for sample in data:
        text = sample['text']
        original_labels = sample.get('labels', [sample.get('label')])
        original_label = original_labels[0]
        
        # Get purely ML prediction/confidence
        # (Using DetectionEngine.predict is safer as it uses pipeline correctly)
        result = DetectionEngine.predict(text)
        
        pred_label = result['label']
        confidence = result['confidence']
        
        # Threshold for auto-fix
        # High confidence implies model found strong patterns
        if confidence > 0.90 and pred_label != original_label:
            
            # Additional Sanity Check: Don't flip to Normal unless 99% sure
            if pred_label == 'Normal' and confidence < 0.98:
                continue
                
            # Logic: If model sees "Medical" with 95% confidence, and label is "Academic", TRUST MODEL.
            # (As seen in "سكل ي ف" example)
            
            sample['labels'] = [pred_label]
            sample['label'] = pred_label
            sample['note'] = f"Auto-Corrected: Model High Confidence ({confidence:.2f}) [{original_label} -> {pred_label}]"
            sample['reviewed_at'] = datetime.now().isoformat()
            
            fixed_count += 1
            # print(f"Fixed: {original_label} -> {pred_label} (Conf: {confidence:.2f})")

    with open(data_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Auto-Corrected {fixed_count} samples based on High Model Confidence.")

if __name__ == "__main__":
    main()
