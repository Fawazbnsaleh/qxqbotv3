"""
Detection Handlers - Production Ready
Monitors messages and detects violations based on enabled categories.
"""
from telegram import Update, ChatMember
from telegram.ext import ContextTypes, MessageHandler, filters
from al_rased.features.detection.engine import DetectionEngine
from al_rased.core.database import (
    get_group,
    get_group_category_status,
    get_category_status,
    get_category_custom_name,
    get_managed_group,
    save_topic,
    get_topic
)
from al_rased.features.group_settings import schedule_message_delete
import logging
import json
import os

# Cache thresholds at module level (loaded once on startup)
THRESHOLDS_FILE = os.path.join(os.path.dirname(__file__), "thresholds.json")
_thresholds_cache = None
_thresholds_mtime = 0

# Cache for admin status (chat_id_user_id -> (is_admin, timestamp))
_admin_cache = {}
_ADMIN_CACHE_TTL = 300  # 5 minutes

# Cache for gray samples topic ID
_gray_topic_id = None

async def get_or_create_gray_topic(context) -> int:
    """Get or create the gray samples topic in training group."""
    global _gray_topic_id
    
    if _gray_topic_id:
        return _gray_topic_id
    
    training_group_id = await get_group("training")
    if not training_group_id:
        return None
    
    # Try to get existing topic
    topic_id = await get_topic("gray_samples", "relabel", training_group_id)
    if topic_id:
        _gray_topic_id = topic_id
        return topic_id
    
    # Create new topic
    try:
        topic = await context.bot.create_forum_topic(
            chat_id=training_group_id, 
            name="🔘 عينات رمادية لإعادة التوسيم"
        )
        topic_id = topic.message_thread_id
        await save_topic("gray_samples", "relabel", topic_id, training_group_id)
        _gray_topic_id = topic_id
        logging.info(f"Created gray samples topic: {topic_id}")
        return topic_id
    except Exception as e:
        logging.error(f"Failed to create gray samples topic: {e}")
        return None

async def send_gray_sample(context, text: str, label: str, confidence: float, source_chat: str):
    """Send a gray/uncertain sample to training group for relabeling."""
    training_group_id = await get_group("training")
    if not training_group_id:
        return
    
    topic_id = await get_or_create_gray_topic(context)
    if not topic_id:
        return
    
    # Truncate if too long
    text_preview = text[:500] + "..." if len(text) > 500 else text
    
    message = (
        f"🔘 **عينة رمادية للمراجعة**\n\n"
        f"📍 المصدر: {source_chat}\n"
        f"🏷 التصنيف المتوقع: {label}\n"
        f"📈 الثقة: {confidence:.0%}\n\n"
        f"📝 النص:\n`{text_preview}`\n\n"
        f"⚡ يرجى التحقق وإعادة التوسيم إذا لزم الأمر."
    )
    
    try:
        await context.bot.send_message(
            chat_id=training_group_id,
            message_thread_id=topic_id,
            text=message,
            parse_mode="Markdown"
        )
        logging.info(f"Sent gray sample to training group: {label} ({confidence:.2f})")
    except Exception as e:
        logging.error(f"Failed to send gray sample: {e}")

# Category labels mapping (Already Arabic, just for formatting/emoji)
CATEGORY_NAMES = {
    "احتيال طبي (عرض)": "🏥 احتيال طبي",
    "احتيال طبي (طلب)": "🏥 احتيال طبي (طلب)",
    "غش أكاديمي (عرض)": "📚 غش أكاديمي",
    "غش أكاديمي (طلب)": "📚 غش أكاديمي (طلب)",
    "تهكير (عرض)": "💻 قرصنة",
    "تهكير (طلب)": "💻 قرصنة (طلب)",
    "احتيال مالي (عرض)": "💰 احتيال مالي",
    "احتيال مالي (طلب)": "💰 احتيال مالي (طلب)",
    "سبام": "📢 سبام",
    "غير أخلاقي (عرض)": "🔞 غير أخلاقي",
    "غير أخلاقي (طلب)": "🔞 غير أخلاقي (طلب)",
}

def get_thresholds():
    """Get thresholds with auto-reload if file changed."""
    global _thresholds_cache, _thresholds_mtime
    
    try:
        current_mtime = os.path.getmtime(THRESHOLDS_FILE)
        
        # Reload if file changed or first load
        if _thresholds_cache is None or current_mtime > _thresholds_mtime:
            with open(THRESHOLDS_FILE, 'r', encoding='utf-8') as f:
                _thresholds_cache = json.load(f)
            _thresholds_mtime = current_mtime
            logging.info(f"Thresholds loaded: {_thresholds_cache}")
    except:
        # Fallback defaults if file missing
            _thresholds_cache = {
                "احتيال طبي (عرض)": 0.46,
                "غش أكاديمي (عرض)": 0.38,
                "تهكير (عرض)": 0.50,
                "احتيال مالي (عرض)": 0.30,
                "سبام": 0.42,
                "غير أخلاقي (عرض)": 0.80,
                # Default for requests
                "احتيال طبي (طلب)": 0.60,
                "غش أكاديمي (طلب)": 0.60,
                "تهكير (طلب)": 0.60,
                "احتيال مالي (طلب)": 0.60,
            }
    
    return _thresholds_cache

async def is_user_admin(chat_id: int, user_id: int, context) -> bool:
    """Check if user is admin in the group with TTL-based caching."""
    import time
    cache_key = f"{chat_id}_{user_id}"
    
    # Check cache first (with TTL)
    if cache_key in _admin_cache:
        cached_value, cached_time = _admin_cache[cache_key]
        if time.time() - cached_time < _ADMIN_CACHE_TTL:
            return cached_value
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        _admin_cache[cache_key] = (is_admin, time.time())
        return is_admin
    except Exception:
        return False

async def get_category_display_name(category: str) -> str:
    """Get display name for category (custom or default)."""
    custom_name = await get_category_custom_name(category)
    if custom_name:
        return custom_name
    return CATEGORY_NAMES.get(category, category)

async def is_detection_enabled(chat_id: int, category: str) -> bool:
    """Check if detection is enabled for this chat and category."""
    
    # 1. Check if category is globally enabled
    global_enabled = await get_category_status(category)
    if not global_enabled:
        return False
    
    # 2. Check if bot is active in this group
    group_info = await get_managed_group(chat_id)
    if group_info:
        if not group_info.get("is_active", True):
            return False
    
    # 3. Check if category is enabled for this specific group
    group_enabled = await get_group_category_status(chat_id, category)
    if not group_enabled:
        return False
    
    return True

async def monitor_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Monitor messages for violations."""
    
    # Ignore commands, empty messages, or non-group chats
    if not update.message or not update.message.text:
        return
    
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Only monitor in groups
    if chat.type not in ["group", "supergroup"]:
        return
    
    chat_id = chat.id
    
    # Skip messages from the LINKED channel only (not any channel)
    # When a channel is linked to a group, messages from that specific channel have sender_chat set
    if message.sender_chat and message.sender_chat.type == "channel":
        # Get the linked channel ID for this group
        try:
            full_chat = await context.bot.get_chat(chat_id)
            linked_channel_id = getattr(full_chat, 'linked_chat_id', None)
            
            # Only skip if this is the linked channel
            if linked_channel_id and message.sender_chat.id == linked_channel_id:
                return
        except Exception:
            pass  # If we can't get linked chat info, proceed with checking
    
    # Skip messages from admins - they are trusted
    if await is_user_admin(chat_id, user.id, context):
        return
    
    # Don't monitor in review group
    review_group_id = await get_group("review")
    
    if review_group_id and chat_id == review_group_id:
        return

    text = update.message.text
    
    # Detect violation
    result = DetectionEngine.predict(text)
    label = result["label"]
    confidence = result["confidence"]
    
    # Skip normal messages
    if label == "طبيعي":
        return
    
    # Check if detection is enabled for this group/category FIRST
    if not await is_detection_enabled(chat_id, label):
        logging.debug(f"Detection disabled for {label} in chat {chat_id}")
        return
    
    # Get threshold for this category
    threshold = get_thresholds().get(label, 0.50)
    
    # Define gray zone: between (threshold - 0.15) and threshold
    gray_lower = max(threshold - 0.15, 0.20)
    
    # Check if this is a gray sample (uncertain)
    if gray_lower <= confidence < threshold:
        # Send to training group for relabeling
        await send_gray_sample(context, text, label, confidence, chat.title or "Unknown")
        return
    
    # Check if confidence meets threshold
    if confidence < threshold:
        return
    
    # Violation Detected!
    
    # Check bot mode
    # If dry_run, we ONLY send report, we do NOT warn or delete
    from al_rased.core.database import get_bot_mode
    mode = await get_bot_mode()
    is_active = mode == "active"
    
    action_taken = "⚠️ رسالة تحذير" if is_active else "🟡 وضع تجريبي (تقرير فقط)"
    
    try:
        # Get localized category name
        category_name = await get_category_display_name(label)
        
        # Only take action in active mode
        if is_active:
            warning_msg = (
                f"🚫 **تنبيه أمني**\n\n"
                f"تم رصد مخالفة محتملة.\n"
                f"**التصنيف:** {category_name}\n"
                f"**الدقة:** {confidence:.0%}\n\n"
                f"نرجو الالتزام بقوانين المجموعة."
            )
            
            sent_msg = await update.message.reply_text(
                warning_msg, 
                quote=True, 
                parse_mode='Markdown'
            )
            
            # Schedule auto-delete if configured for VIP groups
            await schedule_message_delete(context, chat_id, sent_msg.message_id, label)
        else:
            logging.info(f"Dry Run: Violation detected but no action taken in chat {chat_id}")
        
        # Send report to reports group (ALWAYS done, regardless of mode)
        from al_rased.features.admin.handlers import send_violation_report
        await send_violation_report(
            context=context,
            source_chat_id=chat_id,
            source_chat_title=chat.title or "Unknown",
            user_id=user.id,
            username=user.username,
            user_name=user.first_name or "Unknown",
            message_text=text,
            category=category_name,
            confidence=confidence,
            action_taken=action_taken
        )
        
        logging.info(
            f"Violation Detected in chat {chat_id}: {label} ({confidence:.2f}) - "
            f"'{text[:30]}...'"
        )
        
    except Exception as e:
        logging.error(f"Failed to process violation: {e}")

def register_detection_handlers(app):
    """Register detection message handler."""
    # Handle text messages in groups, excluding commands (low priority group=1)
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, 
            monitor_messages
        ), 
        group=1
    )
    logging.info("Detection handlers registered.")
