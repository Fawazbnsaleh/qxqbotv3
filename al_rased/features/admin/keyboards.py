from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import hashlib

# Hash cache for name deletion (maps hash -> name)
_del_name_hash_cache = {}

def _hash_name(name: str) -> str:
    """Generate short hash for name and cache it."""
    h = hashlib.md5(name.encode()).hexdigest()[:8]
    _del_name_hash_cache[h] = name
    return h

def get_name_from_hash(h: str) -> str:
    """Get name from hash cache."""
    return _del_name_hash_cache.get(h)

def get_developer_menu():
    """Main developer menu."""
    keyboard = [
        [InlineKeyboardButton("🤖 الأنظمة الذكية", callback_data="admin_systems")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_systems_menu(categories: list):
    """List of system categories."""
    keyboard = []
    # Create rows of 2 buttons
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(cat.replace("_", " ").title(), callback_data=f"admin_cat_{cat}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_home")])
    return InlineKeyboardMarkup(keyboard)

def get_category_menu(category: str, current_mode: str):
    """Menu for a specific category."""
    # Mode: 'publish' (نشر) or 'stop' (ايقاف)
    # If current is publish, show "Switch to Stop". If stop, show "Switch to Publish".
    # Or just show current status icon.
    
    is_publish = current_mode == "publish"
    toggle_text = "🔄 الوضع: نشر (Active)" if is_publish else "🔄 الوضع: إيقاف (Strict)"
    toggle_action = "stop" if is_publish else "publish"
    
    keyboard = [
        [InlineKeyboardButton(toggle_text, callback_data=f"admin_toggle_{category}_{toggle_action}")],
        [InlineKeyboardButton("🚫 الأسماء الممنوعة", callback_data=f"admin_banned_{category}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_systems")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_banned_names_menu(category: str):
    """Menu for managing banned names."""
    keyboard = [
        [InlineKeyboardButton("➕ إضافة اسم", callback_data=f"admin_add_ban_{category}")],
        [InlineKeyboardButton("➖ حذف اسم", callback_data=f"admin_del_ban_list_{category}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"admin_cat_{category}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_delete_banned_names_menu(category: str, names: list):
    """List of names to delete (uses hash to prevent callback overflow)."""
    keyboard = []
    row = []
    for name in names:
        name_hash = _hash_name(name)
        display = name[:20] + "..." if len(name) > 20 else name
        row.append(InlineKeyboardButton(f"❌ {display}", callback_data=f"admin_del_ban_do_{category}_{name_hash}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"admin_banned_{category}")])
    return InlineKeyboardMarkup(keyboard)
