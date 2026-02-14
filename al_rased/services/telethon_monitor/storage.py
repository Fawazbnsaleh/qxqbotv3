"""
Message Storage Manager - Saves raw messages per group for future use
"""
import json
import os
import re
from datetime import datetime

# Storage directory
MESSAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "group_messages")
MAX_MESSAGES_PER_GROUP = 50000

class MessageStorage:
    def __init__(self):
        os.makedirs(MESSAGES_DIR, exist_ok=True)
        self._file_cache = {}  # Cache file paths
        self._count_cache = {}  # Cache message counts
    
    def _sanitize_filename(self, name: str) -> str:
        """Create safe filename from group name."""
        # Remove/replace unsafe characters
        safe = re.sub(r'[<>:"/\\|?*]', '_', name)
        safe = safe.strip()[:50]  # Limit length
        return safe if safe else "unknown"
    
    def _get_file_path(self, chat_id: int, chat_title: str) -> str:
        """Get file path for a group."""
        if chat_id not in self._file_cache:
            safe_title = self._sanitize_filename(chat_title)
            filename = f"{chat_id}_{safe_title}.json"
            self._file_cache[chat_id] = os.path.join(MESSAGES_DIR, filename)
        return self._file_cache[chat_id]
    
    def _load_messages(self, file_path: str) -> list:
        """Load existing messages from file."""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _get_count(self, chat_id: int, file_path: str) -> int:
        """Get message count for a group (cached)."""
        if chat_id not in self._count_cache:
            messages = self._load_messages(file_path)
            self._count_cache[chat_id] = len(messages)
        return self._count_cache[chat_id]
    
    def save_message(self, chat_id: int, chat_title: str, message_data: dict) -> bool:
        """
        Save a message from a regular member.
        Returns True if saved, False if limit reached.
        """
        file_path = self._get_file_path(chat_id, chat_title)
        
        # Check limit (approximate, by line count or just skip check if too expensive)
        # For performance, we can skip precise count check every time, or cache it.
        # But since we append, we can check file size? 
        # Let's keep using _get_count but optimize it to not load full JSON.
        
        current_count = self._get_count(chat_id, file_path)
        if current_count >= MAX_MESSAGES_PER_GROUP:
            return False
            
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "message_id": message_data.get("message_id"),
            "user_id": message_data.get("user_id"),
            "text": message_data.get("text"),
            "is_member": True
        }
        
        # Append as JSONL (line-delimited JSON) for performance/safety
        # If file doesn't exist or is empty, start fresh.
        # Note: Previous format was a JSON list []. Switching to JSONL is better for appending.
        # But if we must maintain backward compatibility with [], we can't easily append.
        # HYBRID APPROACH: If file ends with ']', seek back and overwrite ']' with ', entry]'
        # BUT JSONL is standard for logs. Let's switch to JSONL for new files, 
        # or just accept list appending overhead?
        # The prompt implies "Fix logical issues". RMW is a logical performance issue.
        # Let's stick to the current format but optimize: 
        # Read file -> if empty "[\n", else seek(-1, 2) to remove ']', write ", \n", then entry, then "]"
        
        mode = 'r+' if os.path.exists(file_path) else 'w'
        try:
            with open(file_path, mode, encoding='utf-8') as f:
                if mode == 'w':
                    f.write("[\n")
                    json.dump(new_entry, f, ensure_ascii=False)
                    f.write("\n]")
                else:
                    # Move to end
                    f.seek(0, 2)
                    size = f.tell()
                    if size > 2: # Not just []
                        f.seek(size - 1) # Overwrite ']'
                        f.write(",\n")
                        json.dump(new_entry, f, ensure_ascii=False)
                        f.write("\n]")
                    else:
                        # Empty list [] case
                        f.seek(0)
                        f.write("[\n")
                        json.dump(new_entry, f, ensure_ascii=False)
                        f.write("\n]")
        except FileNotFoundError:
             with open(file_path, 'w', encoding='utf-8') as f:
                f.write("[\n")
                json.dump(new_entry, f, ensure_ascii=False)
                f.write("\n]")
        
        # Update cache
        self._count_cache[chat_id] = current_count + 1
        
        return True
    
    def get_stats(self) -> dict:
        """Get storage statistics."""
        stats = {}
        for filename in os.listdir(MESSAGES_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(MESSAGES_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    stats[filename] = len(data)
                except:
                    pass
        return stats

# Singleton
message_storage = MessageStorage()
