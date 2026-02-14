"""
Telethon Live Monitor Service
Listens to group messages and runs AI detection in real-time.
Only processes messages from regular members (not admins, not bots).
Saves raw messages per group for future training data.
"""
import asyncio
import logging
import sys
import os
import time

# Add parent paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, ChannelParticipantAdmin, ChannelParticipantCreator

from .config import API_ID, API_HASH, PHONE, SESSION_FILE
from .reports import reports
from .storage import message_storage

# Import detection engine
from features.detection.engine import DetectionEngine
from features.detection.handlers import get_thresholds

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelethonMonitor:
    def __init__(self):
        self.client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        self.running = False
        self.stats = {
            "processed": 0, 
            "violations": 0, 
            "skipped_admin": 0, 
            "skipped_bot": 0,
            "saved_messages": 0,
            "limit_reached": 0
        }
        self._admin_cache = {}  # Cache admins per chat
        self._cache_lock = asyncio.Lock()  # Lock for cache updates to prevent race conditions
        self._cache_last_update = 0
        self._banned_names_cache = {}
        self._system_flags_cache = {}
    
    async def start(self):
        """Start the monitoring service."""
        logger.info("Starting Telethon Monitor...")
        
        await self.client.start(phone=PHONE)
        
        me = await self.client.get_me()
        logger.info(f"Logged in as: {me.first_name} ({me.phone})")
        
        # Get list of groups
        dialogs = await self.client.get_dialogs()
        groups = [d for d in dialogs if d.is_group or d.is_channel]
        logger.info(f"Monitoring {len(groups)} groups/channels")
        
        # Register message handler
        @self.client.on(events.NewMessage(incoming=True))
        async def handle_new_message(event):
            await self._process_message(event)
        
        self.running = True
        logger.info("Monitor is running. Press Ctrl+C to stop.")
        logger.info("Only processing messages from regular members (not admins/bots)")
        logger.info("Saving raw messages per group (max 50,000 per group)")
        
        # Keep running
        await self.client.run_until_disconnected()
    
    async def _is_admin_or_bot(self, chat_id: int, user_id: int, user) -> tuple:
        """Check if user is admin or bot. Returns (is_admin, is_bot)."""
        
        # Check if bot
        if user and getattr(user, 'bot', False):
            return (False, True)
        
        # Check admin status (with caching)
        cache_key = f"{chat_id}_{user_id}"
        
        if cache_key not in self._admin_cache:
            try:
                # Get participant info
                participant = await self.client.get_permissions(chat_id, user_id)
                is_admin = participant.is_admin or participant.is_creator
                self._admin_cache[cache_key] = is_admin
            except Exception as e:
                # If can't check, assume not admin
                self._admin_cache[cache_key] = False
        
        return (self._admin_cache.get(cache_key, False), False)
    
    async def _process_message(self, event):
        """Process incoming message through AI model."""
        try:
            # Get message text
            text = event.message.text
            if not text or len(text) < 10:
                return
            
            # Get chat info
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', 'Private')
            chat_id = event.chat_id
            
            # Skip private chats - only groups/channels
            if not isinstance(chat, (Channel, Chat)):
                return
            
            # Get sender info
            sender = await event.get_sender()
            if not sender:
                return
            
            user_id = sender.id
            
            # Check if admin or bot
            is_admin, is_bot = await self._is_admin_or_bot(chat_id, user_id, sender)
            
            if is_bot:
                self.stats["skipped_bot"] += 1
                return
            
            if is_admin:
                self.stats["skipped_admin"] += 1
                return
            
            # === ONLY REGULAR MEMBERS REACH HERE ===
            
            # Save raw message to per-group file
            saved = message_storage.save_message(
                chat_id=chat_id,
                chat_title=chat_title,
                message_data={
                    "message_id": event.message.id,
                    "user_id": user_id,
                    "text": text[:1000]  # Limit text length
                }
            )
            
            if saved:
                self.stats["saved_messages"] += 1
            else:
                self.stats["limit_reached"] += 1
            
            # Refresh cache every 60s (with lock to prevent race condition)
            from al_rased.core.database import get_all_banned_names_mapping, get_all_system_flags_mapping
            
            if time.time() - self._cache_last_update > 60:
                async with self._cache_lock:
                    # Double-check after acquiring lock
                    if time.time() - self._cache_last_update > 60:
                        self._banned_names_cache = await get_all_banned_names_mapping()
                        self._system_flags_cache = await get_all_system_flags_mapping()
                        self._cache_last_update = time.time()
            
            # 1. Check Forbidden Names (Priority 1)
            name_violation_category = None
            user_full_name = f"{sender.first_name or ''} {sender.last_name or ''} {sender.username or ''}".lower()
            
            for category, keywords in self._banned_names_cache.items():
                for keyword in keywords:
                    if keyword.lower() in user_full_name:
                        name_violation_category = category
                        break
                if name_violation_category:
                    break
            
            # 2. Run ML Prediction (Priority 2)
            ml_violation_category = None
            ml_confidence = 0.0
            
            # Only run ML if no name violation (or run both? Usually Name violation is instant ban)
            # Let's run ML anyway for data collection, but name violation takes precedence for action
            
            # Run AI in executor to prevent blocking
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, DetectionEngine.predict, text)
            label = result["label"]
            confidence = result["confidence"]
            
            # Check threshold
            thresholds = get_thresholds()
            threshold = thresholds.get(label, 0.50)
            is_ml_violation = label != "طبيعي" and confidence >= threshold
            
            if is_ml_violation:
                ml_violation_category = label
                ml_confidence = confidence

            # Save prediction to daily report (stats)
            reports.save_prediction({
                "chat_id": chat_id,
                "chat_title": chat_title,
                "message_id": event.message.id,
                "user_id": user_id,
                "text": text[:500],
                "prediction": label,
                "confidence": confidence,
                "above_threshold": is_ml_violation
            })
            
            self.stats["processed"] += 1

            # Determine Final Violation
            violation_category = name_violation_category or ml_violation_category
            violation_source = "NAME" if name_violation_category else "AI"
            
            if violation_category:
                self.stats["violations"] += 1
                
                # Check Action Mode
                # Default mode: 'publish' (Report Only)
                # 'stop' (Delete + Ban? or just Delete)
                action_mode = self._system_flags_cache.get(f"action_mode:{violation_category}", "publish")
                
                log_msg = f"🚨 VIOLATION ({violation_source}) [{violation_category}] in '{chat_title}'"
                if violation_source == "AI":
                    log_msg += f" ({confidence:.0%})"
                
                logger.info(f"{log_msg}: {text[:50]}...")
                
                if action_mode == "stop":
                    # Attempt to delete message
                    try:
                        await event.delete()
                        logger.info(f"   -> 🗑️ Message deleted (Stop Mode)")
                        
                        # Apply procedures (e.g. Ban) if it's a Name Violation?
                        # User said: "apply procedures on any member whose account contains any word"
                        # Presumably Strict Mode also means Ban.
                        # But be careful with AI false positives.
                        # For Name Violation -> Ban is safer.
                        # For AI -> Maybe just delete?
                        
                        if violation_source == "NAME":
                            # Attempt to ban user
                            try:
                                # Ban for 1 day or forever? Default forever.
                                from telethon.tl.types import ChatBannedRights
                                await self.client.edit_permissions(
                                    chat_id, 
                                    user_id, 
                                    view_messages=False,
                                    until_date=None # Forever
                                )
                                logger.info(f"   -> 🔨 User banned (Name Violation)")
                            except Exception as e:
                                logger.error(f"   -> Failed to ban user: {e}")
                                
                    except Exception as e:
                        logger.error(f"   -> Failed to delete message: {e}")
                
                elif action_mode == "publish":
                     logger.info(f"   -> 📢 Publish Mode (Reported only)")
                     # Could send to a report channel here if configured
            
            # Log progress every 100 messages
            if self.stats["processed"] % 100 == 0:
                logger.info(f"📊 Processed: {self.stats['processed']}, Violations: {self.stats['violations']}, Saved: {self.stats['saved_messages']}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
    
    def get_stats(self):
        """Get current stats."""
        return {
            **self.stats,
            "report_stats": reports.get_stats(),
            "storage_stats": message_storage.get_stats()
        }

async def main():
    """Main entry point."""
    monitor = TelethonMonitor()
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("Stopping monitor...")
    finally:
        stats = monitor.get_stats()
        logger.info(f"Final stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
