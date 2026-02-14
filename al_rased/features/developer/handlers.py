"""
Developer Menu Handlers
Interactive menu for the developer in private chat.
"""
import os
import re
import logging
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, 
    CommandHandler, 
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from core.database import (
    get_category_status, 
    set_category_status,
    get_banned_names,
    add_banned_name,
    remove_banned_name,
    get_banned_names_count,
    get_category_custom_name,
    set_category_custom_name,
    get_prohibited_keywords,
    add_prohibited_keyword,
    remove_prohibited_keyword,
    get_prohibited_keywords_count
)

# Developer ID from environment
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "0"))

# Categories
CATEGORIES = [
    ("احتيال طبي (عرض)", "🏥 احتيال طبي"),
    ("احتيال طبي (طلب)", "🏥 احتيال طبي (طلب)"),
    ("غش أكاديمي (عرض)", "📚 غش أكاديمي"),
    ("غش أكاديمي (طلب)", "📚 غش أكاديمي (طلب)"),
    ("تهكير (عرض)", "💻 قرصنة"),
    ("تهكير (طلب)", "💻 قرصنة (طلب)"),
    ("احتيال مالي (عرض)", "💰 احتيال مالي"),
    ("احتيال مالي (طلب)", "💰 احتيال مالي (طلب)"),
    ("سبام", "📢 سبام"),
    ("غير أخلاقي (عرض)", "🔞 غير أخلاقي"),
    ("غير أخلاقي (طلب)", "🔞 غير أخلاقي (طلب)"),
]

# Conversation states
WAITING_FOR_NAME_TO_ADD = 1
WAITING_FOR_NAME_TO_REMOVE = 2
WAITING_FOR_CATEGORY_RENAME = 3
WAITING_FOR_KEYWORD_TO_ADD = 4
WAITING_FOR_KEYWORD_TO_REMOVE = 5

# Max lengths
MAX_NAME_LENGTH = 100
MAX_CATEGORY_NAME_LENGTH = 50

# Store name hash -> name mapping for deletion (memory-safe with limit)
name_hash_cache = {}
MAX_CACHE_SIZE = 1000

def get_name_hash(name: str) -> str:
    """Generate short hash for name to use in callback data."""
    return hashlib.md5(name.encode()).hexdigest()[:8]

def cache_name(name: str) -> str:
    """Cache name and return its hash."""
    global name_hash_cache
    # Limit cache size
    if len(name_hash_cache) >= MAX_CACHE_SIZE:
        # Remove oldest entries (first 100)
        keys_to_remove = list(name_hash_cache.keys())[:100]
        for key in keys_to_remove:
            del name_hash_cache[key]
    
    name_hash = get_name_hash(name)
    name_hash_cache[name_hash] = name
    return name_hash

def get_cached_name(name_hash: str) -> str:
    """Get name from cache by hash."""
    return name_hash_cache.get(name_hash)

def is_developer(user_id: int) -> bool:
    """Check if user is the developer."""
    if DEVELOPER_ID == 0:
        logging.warning("DEVELOPER_ID not set! Denying all access for security.")
        return False  # Changed: deny all if not set
    return user_id == DEVELOPER_ID

async def check_developer_access(update: Update) -> bool:
    """Check developer access for callback queries. Returns True if allowed."""
    user_id = update.effective_user.id
    if not is_developer(user_id):
        if update.callback_query:
            await update.callback_query.answer("⛔ غير مصرح لك", show_alert=True)
        return False
    return True

# ==================== Main Menu ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command in private chat."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Only work in private chat
    if chat.type != "private":
        return
    
    # Check if developer
    if not is_developer(user.id):
        await update.message.reply_text("⛔ هذا البوت مخصص للمطور فقط.")
        return
    
    logging.info(f"Developer {user.id} accessed the menu")
    
    # Fetch real statistics
    from core.database import get_published_categories, get_banned_names, get_bot_mode
    
    categories = await get_published_categories()
    active_count = sum(1 for c in categories if c.get("is_enabled", False))
    
    # Count banned names
    total_banned = 0
    for cat_id, cat_name in CATEGORIES:
        names = await get_banned_names(cat_id)
        total_banned += len(names)
    
    # Get current mode
    mode = await get_bot_mode()
    mode_text = "🟢 تشغيل فعلي" if mode == "active" else "🟡 تشغيل تجريبي (Dry Run)"

    # Welcome message with real stats
    welcome_text = f"""
🤖 **مرحباً بك في لوحة تحكم الراصد**

أهلاً {user.first_name}! 👋

من هنا يمكنك إدارة أنظمة الكشف الذكية وتخصيص إعداداتها.

⚙️ **حالة النظام:** {mode_text}

📊 **الإحصائيات السريعة:**
• الفئات النشطة: {active_count} / {len(CATEGORIES)}
• إجمالي الأسماء الممنوعة: {total_banned}

اختر من القائمة أدناه للبدء:
"""
    
    keyboard = [
        [InlineKeyboardButton("🧠 الأنظمة الذكية", callback_data="smart_systems")],
        [InlineKeyboardButton("⚙️ وضع التشغيل", callback_data="bot_mode_menu")],
        [InlineKeyboardButton("⚡ نظام التفعيل", callback_data="activation_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Smart Systems Menu ====================

async def show_smart_systems_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the smart systems menu."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    text = """
🧠 **الأنظمة الذكية**

هذه الأنظمة تعمل على كشف المخالفات تلقائياً في جميع المجموعات المراقبة.

اختر ما تريد فعله:
"""
    
    keyboard = [
        [InlineKeyboardButton("⚙️ إدارة الأنظمة", callback_data="manage_systems")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== System Management ====================

async def show_system_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of categories to manage."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    text = """
⚙️ **إدارة الأنظمة**

اختر الفئة التي تريد إدارتها:
"""
    
    # Build category buttons with status indicators
    keyboard = []
    for cat_id, cat_name in CATEGORIES:
        status = await get_category_status(cat_id)
        status_icon = "✅" if status else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status_icon} {cat_name}", 
                callback_data=f"cat_{cat_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="smart_systems")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Category Options ====================

async def show_category_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show options for a specific category."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    # Extract category from callback data
    category = query.data.replace("cat_", "")
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return
    
    # Store in context.user_data instead of global dict
    context.user_data["category"] = category
    
    # Get category info
    status = await get_category_status(category)
    banned_count = await get_banned_names_count(category)
    
    # Find display name (custom or default)
    custom_name = await get_category_custom_name(category)
    default_name = next((name for cid, name in CATEGORIES if cid == category), category)
    cat_display = custom_name if custom_name else default_name
    
    status_text = "✅ نشط" if status else "❌ متوقف"
    toggle_text = "❌ إيقاف" if status else "✅ تفعيل"
    
    text = f"""
📋 **إدارة: {cat_display}**

**الحالة:** {status_text}
**الأسماء الممنوعة:** {banned_count} اسم
**الاسم الأصلي:** {default_name}

اختر الإجراء:
"""
    
    keyword_count = await get_prohibited_keywords_count(category)
    
    keyboard = [
        [InlineKeyboardButton(f"🔄 {toggle_text}", callback_data=f"toggle_{category}")],
        [InlineKeyboardButton("✏️ إعادة تسمية", callback_data=f"rename_{category}")],
        [InlineKeyboardButton(f"🔑 الكلمات المحظورة ({keyword_count})", callback_data=f"keywords_{category}")],
        [InlineKeyboardButton("🚫 الأسماء الممنوعة", callback_data=f"banned_{category}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="manage_systems")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Rename Category ====================

async def start_rename_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the rename category flow."""
    if not await check_developer_access(update):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("rename_", "")
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return ConversationHandler.END
    
    context.user_data["category"] = category
    
    # Get current names
    custom_name = await get_category_custom_name(category)
    default_name = next((name for cid, name in CATEGORIES if cid == category), category)
    current_display = custom_name if custom_name else default_name
    
    text = f"""
✏️ **إعادة تسمية الفئة**

**الفئة:** {category}
**الاسم الحالي:** {current_display}
**الاسم الافتراضي:** {default_name}

أرسل الاسم الجديد للفئة.

💡 **ملاحظات:**
• الحد الأقصى: {MAX_CATEGORY_NAME_LENGTH} حرف
• يمكنك استخدام الإيموجي

أرسل /cancel للإلغاء.
"""
    
    keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data=f"cat_{category}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    return WAITING_FOR_CATEGORY_RENAME

async def receive_new_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the new category name."""
    # Check developer access
    if not is_developer(update.effective_user.id):
        return ConversationHandler.END
    
    new_name = update.message.text.strip()
    
    # Validate length
    if len(new_name) > MAX_CATEGORY_NAME_LENGTH:
        await update.message.reply_text(f"⚠️ الاسم طويل جداً. الحد الأقصى {MAX_CATEGORY_NAME_LENGTH} حرف.")
        return WAITING_FOR_CATEGORY_RENAME
    
    if len(new_name) < 2:
        await update.message.reply_text("⚠️ الاسم قصير جداً. يجب أن يكون حرفين على الأقل.")
        return WAITING_FOR_CATEGORY_RENAME
    
    category = context.user_data.get("category")
    if not category:
        await update.message.reply_text("⚠️ خطأ: لم يتم تحديد الفئة. أعد المحاولة.")
        return ConversationHandler.END
    
    # Save the new name
    await set_category_custom_name(category, new_name)
    
    logging.info(f"Developer {update.effective_user.id} renamed {category} to '{new_name}'")
    
    text = f"✅ تم تغيير اسم الفئة إلى: **{new_name}**"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع للفئة", callback_data=f"cat_{category}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    return ConversationHandler.END

# ==================== Toggle Category ====================

async def toggle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle category enabled/disabled status."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    
    # Extract category
    category = query.data.replace("toggle_", "")
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return
    
    # Get current status and toggle
    current_status = await get_category_status(category)
    new_status = not current_status
    await set_category_status(category, new_status)
    
    logging.info(f"Developer {update.effective_user.id} toggled {category} to {new_status}")
    
    status_text = "✅ تم التفعيل" if new_status else "❌ تم الإيقاف"
    await query.answer(status_text, show_alert=True)
    
    # Refresh the category options
    query.data = f"cat_{category}"
    await show_category_options(update, context)

# ==================== Banned Names Menu ====================

async def show_banned_names_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show banned names management menu."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    # Extract category
    category = query.data.replace("banned_", "")
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return
    
    context.user_data["category"] = category
    
    # Get banned names
    banned_names = await get_banned_names(category)
    cat_display = next((name for cid, name in CATEGORIES if cid == category), category)
    
    if banned_names:
        names_list = "\n".join([f"• {name[:50]}..." if len(name) > 50 else f"• {name}" for name in banned_names[:10]])
        if len(banned_names) > 10:
            names_list += f"\n... و {len(banned_names) - 10} أسماء أخرى"
    else:
        names_list = "لا توجد أسماء ممنوعة بعد"
    
    text = f"""
🚫 **الأسماء الممنوعة - {cat_display}**

**الأسماء المسجلة ({len(banned_names)}):**
{names_list}

اختر الإجراء:
"""
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة اسم", callback_data=f"add_name_{category}")],
        [InlineKeyboardButton("➖ حذف اسم", callback_data=f"remove_name_{category}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"cat_{category}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Add Banned Name ====================

async def start_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add name flow."""
    if not await check_developer_access(update):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("add_name_", "")
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return ConversationHandler.END
    
    context.user_data["category"] = category
    context.user_data["action"] = "add"
    
    text = f"""
➕ **إضافة اسم ممنوع**

أرسل الاسم أو الكلمة المراد منعها.

💡 **ملاحظات:**
• الحد الأقصى: {MAX_NAME_LENGTH} حرف
• سيتم تطبيق الإجراءات على أي عضو حسابه يحتوي هذه الكلمة.

أرسل /cancel للإلغاء.
"""
    
    keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data=f"banned_{category}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    return WAITING_FOR_NAME_TO_ADD

async def receive_name_to_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the name to add."""
    # Check developer access
    if not is_developer(update.effective_user.id):
        return ConversationHandler.END
    
    name = update.message.text.strip()
    
    # Input sanitization: remove dangerous characters but keep Arabic and basic punctuation
    name = re.sub(r'[<>\"\';\\]', '', name)  # Remove potential injection chars
    name = name.strip()
    
    # Validate length
    if len(name) > MAX_NAME_LENGTH:
        await update.message.reply_text(f"⚠️ الاسم طويل جداً. الحد الأقصى {MAX_NAME_LENGTH} حرف.")
        return WAITING_FOR_NAME_TO_ADD
    
    if len(name) < 2:
        await update.message.reply_text("⚠️ الاسم قصير جداً. يجب أن يكون حرفين على الأقل.")
        return WAITING_FOR_NAME_TO_ADD
    
    category = context.user_data.get("category")
    if not category:
        await update.message.reply_text("⚠️ خطأ: لم يتم تحديد الفئة. أعد المحاولة.")
        return ConversationHandler.END
    
    # Add the name
    success = await add_banned_name(category, name)
    
    if success:
        text = f"✅ تم إضافة الاسم: **{name}**"
        logging.info(f"Developer {update.effective_user.id} added banned name '{name}' to {category}")
    else:
        text = f"⚠️ الاسم **{name}** موجود مسبقاً"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data=f"banned_{category}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    return ConversationHandler.END

# ==================== Remove Banned Name ====================

async def start_remove_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the remove name flow."""
    if not await check_developer_access(update):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("remove_name_", "")
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return ConversationHandler.END
    
    context.user_data["category"] = category
    context.user_data["action"] = "remove"
    
    # Get current banned names
    banned_names = await get_banned_names(category)
    
    if not banned_names:
        await query.answer("لا توجد أسماء للحذف", show_alert=True)
        return ConversationHandler.END
    
    # Show names as buttons with hash for safe callback data
    keyboard = []
    for name in banned_names[:20]:  # Limit to 20
        name_hash = cache_name(name)
        display_name = name[:30] + "..." if len(name) > 30 else name
        keyboard.append([InlineKeyboardButton(f"🗑️ {display_name}", callback_data=f"del_{category}_{name_hash}")])
    
    keyboard.append([InlineKeyboardButton("🔙 إلغاء", callback_data=f"banned_{category}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
➖ **حذف اسم ممنوع**

اختر الاسم المراد حذفه:
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    return WAITING_FOR_NAME_TO_REMOVE

async def confirm_remove_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and remove the name."""
    if not await check_developer_access(update):
        return ConversationHandler.END
    
    query = update.callback_query
    
    # Parse del_category_namehash
    parts = query.data.split("_", 2)
    if len(parts) < 3:
        await query.answer("خطأ", show_alert=True)
        return ConversationHandler.END
    
    category = parts[1]
    name_hash = parts[2]
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return ConversationHandler.END
    
    # Get name from hash
    name = get_cached_name(name_hash)
    if not name:
        await query.answer("⚠️ انتهت صلاحية الجلسة. أعد المحاولة.", show_alert=True)
        query.data = f"banned_{category}"
        await show_banned_names_menu(update, context)
        return ConversationHandler.END
    
    # Remove the name
    success = await remove_banned_name(category, name)
    
    if success:
        await query.answer(f"✅ تم حذف: {name[:30]}", show_alert=True)
        logging.info(f"Developer {update.effective_user.id} removed banned name '{name}' from {category}")
    else:
        await query.answer("⚠️ لم يتم العثور على الاسم", show_alert=True)
    
    # Refresh banned names menu
    query.data = f"banned_{category}"
    await show_banned_names_menu(update, context)
    
    return ConversationHandler.END

# ==================== Prohibited Keywords Menu ====================

async def show_keywords_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show prohibited keywords management menu."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    # Extract category
    category = query.data.replace("keywords_", "")
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return
    
    context.user_data["category"] = category
    
    # Get keywords
    keywords = await get_prohibited_keywords(category)
    cat_display = next((name for cid, name in CATEGORIES if cid == category), category)
    
    if keywords:
        keywords_list = "\n".join([f"• {kw}" for kw in keywords[:15]])
        if len(keywords) > 15:
            keywords_list += f"\n... و {len(keywords) - 15} كلمات أخرى"
    else:
        keywords_list = "لا توجد كلمات محظورة بعد"
    
    text = f"""
🔑 **الكلمات المحظورة - {cat_display}**

**الكلمات المسجلة ({len(keywords)}):**
{keywords_list}

💡 الكلمات المحظورة تُكتشف فوراً بنسبة 95% بدون الحاجة للنموذج.

اختر الإجراء:
"""
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة كلمة", callback_data=f"add_kw_{category}")],
        [InlineKeyboardButton("➖ حذف كلمة", callback_data=f"remove_kw_{category}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"cat_{category}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Add Prohibited Keyword ====================

async def start_add_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add keyword flow."""
    if not await check_developer_access(update):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("add_kw_", "")
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return ConversationHandler.END
    
    context.user_data["category"] = category
    
    text = f"""
➕ **إضافة كلمة محظورة**

أرسل الكلمة أو العبارة المراد حظرها.

💡 **ملاحظات:**
• الحد الأقصى: 50 حرف
• أي رسالة تحتوي هذه الكلمة ستُكتشف فوراً

أرسل /cancel للإلغاء.
"""
    
    keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data=f"keywords_{category}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    return WAITING_FOR_KEYWORD_TO_ADD

async def receive_keyword_to_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive the keyword to add."""
    if not is_developer(update.effective_user.id):
        return ConversationHandler.END
    
    keyword = update.message.text.strip()
    
    # Input sanitization
    keyword = re.sub(r'[<>\"\';\\\\]', '', keyword)
    keyword = keyword.strip()
    
    # Validate length
    if len(keyword) > 50:
        await update.message.reply_text("⚠️ الكلمة طويلة جداً. الحد الأقصى 50 حرف.")
        return WAITING_FOR_KEYWORD_TO_ADD
    
    if len(keyword) < 2:
        await update.message.reply_text("⚠️ الكلمة قصيرة جداً. يجب أن تكون حرفين على الأقل.")
        return WAITING_FOR_KEYWORD_TO_ADD
    
    category = context.user_data.get("category")
    if not category:
        await update.message.reply_text("⚠️ خطأ: لم يتم تحديد الفئة. أعد المحاولة.")
        return ConversationHandler.END
    
    # Add the keyword
    success = await add_prohibited_keyword(category, keyword)
    
    if success:
        text = f"✅ تم إضافة الكلمة: **{keyword}**"
        logging.info(f"Developer {update.effective_user.id} added keyword '{keyword}' to {category}")
    else:
        text = f"⚠️ الكلمة **{keyword}** موجودة مسبقاً"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع للقائمة", callback_data=f"keywords_{category}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    return ConversationHandler.END

# ==================== Remove Prohibited Keyword ====================

async def start_remove_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the remove keyword flow."""
    if not await check_developer_access(update):
        return ConversationHandler.END
    
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("remove_kw_", "")
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return ConversationHandler.END
    
    context.user_data["category"] = category
    
    # Get current keywords
    keywords = await get_prohibited_keywords(category)
    
    if not keywords:
        await query.answer("لا توجد كلمات للحذف", show_alert=True)
        return ConversationHandler.END
    
    # Show keywords as buttons
    keyboard = []
    for kw in keywords[:20]:  # Limit to 20
        kw_hash = cache_name(kw)
        display_kw = kw[:25] + "..." if len(kw) > 25 else kw
        keyboard.append([InlineKeyboardButton(f"🗑️ {display_kw}", callback_data=f"delkw_{category}_{kw_hash}")])
    
    keyboard.append([InlineKeyboardButton("🔙 إلغاء", callback_data=f"keywords_{category}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
➖ **حذف كلمة محظورة**

اختر الكلمة المراد حذفها:
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    return WAITING_FOR_KEYWORD_TO_REMOVE

async def confirm_remove_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and remove the keyword."""
    if not await check_developer_access(update):
        return ConversationHandler.END
    
    query = update.callback_query
    
    # Parse delkw_category_kwhash
    parts = query.data.split("_", 2)
    if len(parts) < 3:
        await query.answer("خطأ", show_alert=True)
        return ConversationHandler.END
    
    category = parts[1]
    kw_hash = parts[2]
    
    # Validate category
    valid_categories = [c[0] for c in CATEGORIES]
    if category not in valid_categories:
        await query.answer("فئة غير صالحة", show_alert=True)
        return ConversationHandler.END
    
    # Get keyword from hash
    keyword = get_cached_name(kw_hash)
    if not keyword:
        await query.answer("⚠️ انتهت صلاحية الجلسة. أعد المحاولة.", show_alert=True)
        query.data = f"keywords_{category}"
        await show_keywords_menu(update, context)
        return ConversationHandler.END
    
    # Remove the keyword
    success = await remove_prohibited_keyword(category, keyword)
    
    if success:
        await query.answer(f"✅ تم حذف: {keyword[:20]}", show_alert=True)
        logging.info(f"Developer {update.effective_user.id} removed keyword '{keyword}' from {category}")
    else:
        await query.answer("⚠️ لم يتم العثور على الكلمة", show_alert=True)
    
    # Refresh keywords menu
    query.data = f"keywords_{category}"
    await show_keywords_menu(update, context)
    
    return ConversationHandler.END

# ==================== Back to Main ====================

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    welcome_text = f"""
🤖 **مرحباً بك في لوحة تحكم الراصد**

أهلاً {user.first_name}! 👋

من هنا يمكنك إدارة أنظمة الكشف الذكية وتخصيص إعداداتها.

اختر من القائمة أدناه للبدء:
"""
    
    keyboard = [
        [InlineKeyboardButton("🧠 الأنظمة الذكية", callback_data="smart_systems")],
        [InlineKeyboardButton("⚡ نظام التفعيل", callback_data="activation_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Cancel Command ====================

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation."""
    # Clear user data
    context.user_data.clear()
    
    await update.message.reply_text("❌ تم الإلغاء")
    return ConversationHandler.END

# ==================== Register Handlers ====================

def register_developer_handlers(app):
    """Register all developer menu handlers."""
    
    # Start command (only in private)
    app.add_handler(CommandHandler("start", start_command, filters=filters.ChatType.PRIVATE))
    
    # Callback query handlers
    app.add_handler(CallbackQueryHandler(show_smart_systems_menu, pattern="^smart_systems$"))
    app.add_handler(CallbackQueryHandler(show_system_management, pattern="^manage_systems$"))
    app.add_handler(CallbackQueryHandler(show_category_options, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(toggle_category, pattern="^toggle_"))
    app.add_handler(CallbackQueryHandler(show_banned_names_menu, pattern="^banned_"))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    
    # Conversation handler for adding names
    add_name_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_name, pattern="^add_name_")],
        states={
            WAITING_FOR_NAME_TO_ADD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name_to_add)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(show_banned_names_menu, pattern="^banned_")
        ],
        per_message=False
    )
    app.add_handler(add_name_conv)
    
    # Conversation handler for removing names
    remove_name_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_remove_name, pattern="^remove_name_")],
        states={
            WAITING_FOR_NAME_TO_REMOVE: [
                CallbackQueryHandler(confirm_remove_name, pattern="^del_")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(show_banned_names_menu, pattern="^banned_")
        ],
        per_message=False
    )
    app.add_handler(remove_name_conv)
    
    # Conversation handler for renaming categories
    rename_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_rename_category, pattern="^rename_")],
        states={
            WAITING_FOR_CATEGORY_RENAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_category_name)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(show_category_options, pattern="^cat_")
        ],
        per_message=False
    )
    app.add_handler(rename_conv)
    
    # Callback handler for keywords menu
    app.add_handler(CallbackQueryHandler(show_keywords_menu, pattern="^keywords_"))
    
    # Conversation handler for adding keywords
    add_keyword_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_keyword, pattern="^add_kw_")],
        states={
            WAITING_FOR_KEYWORD_TO_ADD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_keyword_to_add)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(show_keywords_menu, pattern="^keywords_")
        ],
        per_message=False
    )
    app.add_handler(add_keyword_conv)
    
    # Conversation handler for removing keywords
    remove_keyword_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_remove_keyword, pattern="^remove_kw_")],
        states={
            WAITING_FOR_KEYWORD_TO_REMOVE: [
                CallbackQueryHandler(confirm_remove_keyword, pattern="^delkw_")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(show_keywords_menu, pattern="^keywords_")
        ],
        per_message=False
    )
    app.add_handler(remove_keyword_conv)

    
    # Mode settings handlers
    app.add_handler(CallbackQueryHandler(show_mode_settings, pattern="^bot_mode_menu$"))
    app.add_handler(CallbackQueryHandler(handle_mode_change, pattern="^set_mode_"))

    logging.info("Developer menu handlers registered.")

# ==================== Bot Mode Handlers ====================

async def show_mode_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot operation mode settings."""
    if not is_developer(update.effective_user.id):
        return

    query = update.callback_query
    await query.answer()

    from core.database import get_bot_mode
    mode = await get_bot_mode()
    
    is_active = mode == "active"
    status_emoji = "🟢" if is_active else "🟡"
    status_text = "تشغيل فعلي" if is_active else "تشغيل تجريبي (Dry Run)"
    
    desc = """
**🟢 الوضع الفعلي:**
يقوم البوت باتخاذ الإجراءات (حذف رسائل التحذير بعد وقت محدد، إرسال تنبيهات للمستخدمين).

**🟡 الوضع التجريبي (Dry Run):**
يقوم البوت بالكشف وإرسال التقارير لقروب التقارير فقط. 
**لا يتم** إرسال تحذيرات للمستخدمين في القروبات.
"""

    text = f"""
⚙️ **إعدادات وضع التشغيل**

الحالة الحالية: {status_emoji} **{status_text}**

{desc}
"""

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'🔘' if is_active else '⚪️'} تفعيل فعلي", 
                callback_data="set_mode_active"
            ),
            InlineKeyboardButton(
                f"{'🔘' if not is_active else '⚪️'} وضع تجريبي", 
                callback_data="set_mode_dryrun"
            )
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data="developer_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def handle_mode_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle changing bot mode."""
    if not is_developer(update.effective_user.id):
        return

    query = update.callback_query
    action = query.data.replace("set_mode_", "")
    
    from core.database import set_bot_mode
    
    if action == "active":
        await set_bot_mode("active")
        await query.answer("✅ تم التبديل إلى الوضع الفعلي")
    elif action == "dryrun":
        await set_bot_mode("dry_run")
        await query.answer("✅ تم التبديل إلى الوضع التجريبي")
    
    # Refresh view
    await show_mode_settings(update, context)
