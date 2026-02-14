"""
Reports Manager - Saves prediction reports for model improvement
"""
import json
import os
from datetime import datetime
from .config import REPORTS_DIR

class ReportsManager:
    def __init__(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        self.current_file = None
        self.current_date = None
        self._init_report_file()
    
    def _init_report_file(self):
        """Create daily report file."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if self.current_date != today:
            self.current_date = today
            self.current_file = os.path.join(REPORTS_DIR, f"report_{today}.json")
            
            if not os.path.exists(self.current_file):
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
    
    def save_prediction(self, message_data: dict):
        """Save a prediction to today's report (Append mode)."""
        self._init_report_file()
        
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "chat_id": message_data.get("chat_id"),
            "chat_title": message_data.get("chat_title"),
            "message_id": message_data.get("message_id"),
            "text": message_data.get("text"),
            "prediction": message_data.get("prediction"),
            "confidence": message_data.get("confidence"),
            "above_threshold": message_data.get("above_threshold", False)
        }
        
        # Append optimization (same as storage.py)
        file_path = self.current_file
        mode = 'r+' if os.path.exists(file_path) else 'w'
        
        try:
            with open(file_path, mode, encoding='utf-8') as f:
                if mode == 'w':
                    f.write("[\n")
                    json.dump(new_entry, f, ensure_ascii=False)
                    f.write("\n]")
                else:
                    f.seek(0, 2)
                    size = f.tell()
                    if size > 2:
                        f.seek(size - 1)
                        f.write(",\n")
                        json.dump(new_entry, f, ensure_ascii=False)
                        f.write("\n]")
                    else:
                        f.seek(0)
                        f.write("[\n")
                        json.dump(new_entry, f, ensure_ascii=False)
                        f.write("\n]")
        except FileNotFoundError:
             with open(file_path, 'w', encoding='utf-8') as f:
                f.write("[\n")
                json.dump(new_entry, f, ensure_ascii=False)
                f.write("\n]")
        
        return 1 # Just return constant, we don't need exact length for reports
    
    def get_stats(self):
        """Get today's stats."""
        self._init_report_file()
        
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = []
        
        total = len(data)
        violations = sum(1 for d in data if d.get("above_threshold"))
        
        return {
            "total": total,
            "violations": violations,
            "normal": total - violations
        }

# Singleton
reports = ReportsManager()
