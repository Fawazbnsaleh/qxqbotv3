"""
Group Settings Handlers
Settings menu for group admins to manage smart detection systems.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    ContextTypes, 
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from al_rased.core.database import (
    get_category_status,
    get_group_category_status,
    set_group_category_status,
    get_published_categories,
    get_category_custom_name,
    is_group_vip,
    get_notification_delete_time,
    set_notification_delete_time
)

import os
import asyncio
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "0"))

# ==================== Auto-Delete Helper ====================

async def schedule_message_delete(context, chat_id: int, message_id: int, category: str):
    """Schedule a message to be deleted after the configured time for the group/category."""
    delete_time = await get_notification_delete_time(chat_id, category)
    
    if delete_time <= 0:
        return  # No auto-delete configured
    
    async def delete_after_delay():
        await asyncio.sleep(delete_time)
        try:
            await context.bot.delete_message(chat_id, message_id)
        except Exception:
            pass  # Message might already be deleted
    
    # Run in background
    asyncio.create_task(delete_after_delay())

# Categories with Arabic names
# Categories with Arabic names (Keys must match DetectionEngine output)
CATEGORIES = {
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

# Cache for admin status (group_id_user_id -> (is_admin, timestamp))
import time as _time
admin_cache = {}
ADMIN_CACHE_TTL = 300  # 5 minutes

async def is_admin(chat_id: int, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is admin in the group with TTL-based caching."""
    cache_key = f"{chat_id}_{user_id}"
    
    # Check cache first (with TTL)
    if cache_key in admin_cache:
        cached_value, cached_time = admin_cache[cache_key]
        if _time.time() - cached_time < ADMIN_CACHE_TTL:
            return cached_value
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        is_admin_result = member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        admin_cache[cache_key] = (is_admin_result, _time.time())
        return is_admin_result
    except Exception as e:
        logging.error(f"Failed to check admin status: {e}")
        return False

async def check_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: int) -> bool:
    """Check admin access for callback queries. Returns True if allowed."""
    user_id = update.effective_user.id
    
    if not await is_admin(group_id, user_id, context):
        if update.callback_query:
            await update.callback_query.answer("⛔ هذا الإجراء متاح للمشرفين فقط", show_alert=True)
        return False
    return True

def validate_category(category: str) -> bool:
    """Validate that category is in the allowed list."""
    return category in CATEGORIES

# ==================== Settings Command ====================

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'الاعدادات' command in groups."""
    chat = update.effective_chat
    user = update.effective_user
    
    # Only work in groups
    if chat.type not in ["group", "supergroup"]:
        return
    
    # Check if admin
    if not await is_admin(chat.id, user.id, context):
        await update.message.reply_text("⛔ هذا الأمر متاح للمشرفين فقط.")
        return
    
    logging.info(f"Admin {user.id} accessed settings in group {chat.id}")
    
    text = f"""
⚙️ **إعدادات القروب**

مرحباً! من هنا يمكنك التحكم في إعدادات أنظمة الكشف الذكية لهذا القروب.

📍 **القروب:** {chat.title}
"""
    
    keyboard = [
        [InlineKeyboardButton("🧠 الأنظمة الذكية", callback_data=f"gs_systems_{chat.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Smart Systems List ====================

async def show_group_systems(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of published systems for the group."""
    query = update.callback_query
    
    # Extract group_id from callback
    try:
        group_id = int(query.data.replace("gs_systems_", ""))
    except ValueError:
        await query.answer("خطأ في البيانات", show_alert=True)
        return
    
    # Check admin access
    if not await check_admin_callback(update, context, group_id):
        return
    
    await query.answer()
    
    text = """
🧠 **الأنظمة الذكية المتاحة**

اختر النظام للتحكم فيه:
"""
    
    keyboard = []
    for cat_id in CATEGORIES.keys():
        default_name = CATEGORIES[cat_id]
        
        # Check global status
        global_status = await get_category_status(cat_id)
        if not global_status:
            continue  # Skip globally disabled categories
        
        # Get custom name if set
        custom_name = await get_category_custom_name(cat_id)
        cat_name = custom_name if custom_name else default_name
        
        # Check group-specific status
        group_status = await get_group_category_status(group_id, cat_id)
        status_icon = "✅" if group_status else "❌"
        
        keyboard.append([
            InlineKeyboardButton(
                f"{status_icon} {cat_name}",
                callback_data=f"gs_cat_{group_id}_{cat_id}"
            )
        ])
    
    if not keyboard:
        text = """
🧠 **الأنظمة الذكية**

⚠️ لا توجد أنظمة منشورة حالياً.
يرجى التواصل مع المطور لتفعيل الأنظمة.
"""
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"gs_back_{group_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Category Options ====================

async def show_group_category_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show options for a specific category in group."""
    query = update.callback_query
    
    # Parse: gs_cat_groupid_categoryname
    parts = query.data.split("_", 3)
    if len(parts) < 4:
        await query.answer("خطأ في البيانات", show_alert=True)
        return
    
    try:
        group_id = int(parts[2])
    except ValueError:
        await query.answer("خطأ في البيانات", show_alert=True)
        return
    
    category = parts[3]
    
    # Validate category
    if not validate_category(category):
        await query.answer("فئة غير صالحة", show_alert=True)
        return
    
    # Check admin access
    if not await check_admin_callback(update, context, group_id):
        return
    
    await query.answer()
    
    # Get status
    status = await get_group_category_status(group_id, category)
    cat_name = CATEGORIES.get(category, category)
    
    status_text = "✅ مفعّل" if status else "❌ معطّل"
    toggle_text = "❌ تعطيل" if status else "✅ تفعيل"
    
    text = f"""
📋 **{cat_name}**

**الحالة في هذا القروب:** {status_text}

عند التفعيل، سيقوم النظام بمراقبة الرسائل وكشف المخالفات المتعلقة بهذه الفئة تلقائياً.
"""
    
    keyboard = [
        [InlineKeyboardButton(f"🔄 {toggle_text}", callback_data=f"gs_toggle_{group_id}_{category}")],
        [InlineKeyboardButton("🔔 الإشعارات", callback_data=f"gs_notif_{group_id}_{category}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"gs_systems_{group_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Toggle Category ====================

async def toggle_group_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle category status for group."""
    query = update.callback_query
    
    # Parse: gs_toggle_groupid_category
    parts = query.data.split("_", 3)
    if len(parts) < 4:
        await query.answer("خطأ في البيانات", show_alert=True)
        return
    
    try:
        group_id = int(parts[2])
    except ValueError:
        await query.answer("خطأ في البيانات", show_alert=True)
        return
    
    category = parts[3]
    
    # Validate category
    if not validate_category(category):
        await query.answer("فئة غير صالحة", show_alert=True)
        return
    
    # Check admin access
    if not await check_admin_callback(update, context, group_id):
        return
    
    # Get current and toggle
    current = await get_group_category_status(group_id, category)
    new_status = not current
    await set_group_category_status(group_id, category, new_status)
    
    logging.info(f"Admin {update.effective_user.id} toggled {category} to {new_status} in group {group_id}")
    
    status_msg = "✅ تم التفعيل" if new_status else "❌ تم التعطيل"
    await query.answer(status_msg, show_alert=True)
    
    # Refresh category options
    query.data = f"gs_cat_{group_id}_{category}"
    await show_group_category_options(update, context)

# ==================== Back to Settings ====================

async def back_to_group_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main group settings."""
    query = update.callback_query
    
    # Extract group_id
    try:
        group_id = int(query.data.replace("gs_back_", ""))
    except ValueError:
        await query.answer("خطأ في البيانات", show_alert=True)
        return
    
    # Check admin access
    if not await check_admin_callback(update, context, group_id):
        return
    
    await query.answer()
    
    try:
        chat = await context.bot.get_chat(group_id)
        chat_title = chat.title
    except Exception:
        chat_title = "القروب"
    
    text = f"""
⚙️ **إعدادات القروب**

📍 **القروب:** {chat_title}
"""
    
    keyboard = [
        [InlineKeyboardButton("🧠 الأنظمة الذكية", callback_data=f"gs_systems_{group_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Register Handlers ====================

# ==================== Notifications Settings ====================

async def show_notifications_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة الإشعارات - مختلف حسب VIP."""
    query = update.callback_query
    
    # Parse: gs_notif_groupid_category
    parts = query.data.split("_", 3)
    if len(parts) < 4:
        await query.answer("خطأ", show_alert=True)
        return
    
    try:
        group_id = int(parts[2])
    except ValueError:
        await query.answer("خطأ", show_alert=True)
        return
    
    category = parts[3]
    
    if not validate_category(category):
        await query.answer("فئة غير صالحة", show_alert=True)
        return
    
    if not await check_admin_callback(update, context, group_id):
        return
    
    await query.answer()
    
    # Check VIP status
    vip = await is_group_vip(group_id)
    cat_name = CATEGORIES.get(category, category)
    
    if not vip:
        # Not VIP - show upgrade message
        text = f"""
🔔 **إشعارات {cat_name}**

⚠️ **هذه الميزة متاحة فقط للقروبات VIP المدفوعة**

يمكنك التواصل مع المطور لتفعيل البوت بالنسخة المدفوعة والحصول على:
• التحكم في حذف رسائل التحذير تلقائياً
• إعدادات متقدمة لكل فئة
• دعم فني مباشر
"""
        keyboard = []
        if DEVELOPER_ID:
            keyboard.append([InlineKeyboardButton("💬 التواصل مع المطور", url=f"tg://user?id={DEVELOPER_ID}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"gs_cat_{group_id}_{category}")])
    else:
        # VIP - show settings
        delete_time = await get_notification_delete_time(group_id, category)
        
        if delete_time == 0:
            time_text = "لا يتم الحذف"
        else:
            time_text = f"{delete_time} ثانية"
        
        text = f"""
🔔 **إشعارات {cat_name}**

⭐ **قروب مميز VIP**

مرحباً! هذا القروب مشترك في النسخة المدفوعة ويمكنك التحكم في إعدادات الإشعارات.  

🗑 **حذف رسالة التحذير بعد:** {time_text}
"""
        keyboard = [
            [InlineKeyboardButton("🗑 حذف الرسالة بعد...", callback_data=f"gs_deltime_{group_id}_{category}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"gs_cat_{group_id}_{category}")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Delete Timer Settings ====================

async def show_delete_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إعدادات وقت الحذف."""
    query = update.callback_query
    
    parts = query.data.split("_", 3)
    if len(parts) < 4:
        await query.answer("خطأ", show_alert=True)
        return
    
    try:
        group_id = int(parts[2])
    except ValueError:
        await query.answer("خطأ", show_alert=True)
        return
    
    category = parts[3]
    
    # Validate category
    if not validate_category(category):
        await query.answer("فئة غير صالحة", show_alert=True)
        return
    
    if not await check_admin_callback(update, context, group_id):
        return
    
    # Check VIP status - only VIP groups can access this
    if not await is_group_vip(group_id):
        await query.answer("⚠️ هذه الميزة للقروبات VIP فقط", show_alert=True)
        return
    
    await query.answer()
    
    current_time = await get_notification_delete_time(group_id, category)
    cat_name = CATEGORIES.get(category, category)
    
    if current_time == 0:
        time_text = "لا يتم الحذف"
    else:
        time_text = f"{current_time} ثانية"
    
    text = f"""
🗑 **حذف رسالة التحذير - {cat_name}**

**الوقت الحالي:** {time_text}

اختر المدة التي يتم بعدها حذف رسالة التحذير:
"""
    
    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data=f"gs_dt_dec_{group_id}_{category}"),
            InlineKeyboardButton(f"  {current_time}s  ", callback_data="gs_dt_current"),
            InlineKeyboardButton("➕", callback_data=f"gs_dt_inc_{group_id}_{category}")
        ],
        [
            InlineKeyboardButton("❌ لا حذف", callback_data=f"gs_ds_{group_id}_{category}_0"),
            InlineKeyboardButton("5s", callback_data=f"gs_ds_{group_id}_{category}_5"),
            InlineKeyboardButton("10s", callback_data=f"gs_ds_{group_id}_{category}_10")
        ],
        [
            InlineKeyboardButton("30s", callback_data=f"gs_ds_{group_id}_{category}_30"),
            InlineKeyboardButton("60s", callback_data=f"gs_ds_{group_id}_{category}_60"),
            InlineKeyboardButton("120s", callback_data=f"gs_ds_{group_id}_{category}_120")
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"gs_notif_{group_id}_{category}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def adjust_delete_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعديل وقت الحذف."""
    query = update.callback_query
    data = query.data
    
    # Parse the action and values
    if data == "gs_dt_current":
        await query.answer()
        return
    
    elif query.data.startswith("gs_ds_"):
        # Set delete timer directly from predefined buttons
        parts = query.data.split("_")
        # Expected format: gs_ds_GROUPID_CATEGORY_SECONDS
        
        try:
            group_id = int(parts[2])
            seconds = int(parts[-1])
            # Category is everything between group_id and seconds
            category = "_".join(parts[3:-1])
        except (ValueError, IndexError):
            await query.answer("خطأ في البيانات", show_alert=True)
            return
        
        if not await check_admin_callback(update, context, group_id):
            return
        
        # Validate category
        if not validate_category(category):
            await query.answer("فئة غير صالحة", show_alert=True)
            return
        
        # Check VIP status - only VIP groups can modify
        if not await is_group_vip(group_id):
            await query.answer("⚠️ هذه الميزة للقروبات VIP فقط", show_alert=True)
            return
        
        await set_notification_delete_time(group_id, category, seconds)
        logging.info(f"Group {group_id} set delete time for {category} to {seconds}s via direct set button")
        
        await query.answer(f"✅ {seconds}s")
        
        # Refresh view
        query.data = f"gs_deltime_{group_id}_{category}"
        await show_delete_timer(update, context)
        return # Added return to prevent further processing
    
    # gs_dt_action_groupid_category or gs_dt_set_groupid_category_value
    parts = data.split("_")
    
    if len(parts) < 5:
        await query.answer("خطأ", show_alert=True)
        return
    
    action = parts[2]
    
    try:
        group_id = int(parts[3])
        category = parts[4]
    except (ValueError, IndexError):
        await query.answer("خطأ", show_alert=True)
        return
    
    if not await check_admin_callback(update, context, group_id):
        return
    
    # Validate category
    if not validate_category(category):
        await query.answer("فئة غير صالحة", show_alert=True)
        return
    
    # Check VIP status - only VIP groups can modify
    if not await is_group_vip(group_id):
        await query.answer("⚠️ هذه الميزة للقروبات VIP فقط", show_alert=True)
        return
    
    current = await get_notification_delete_time(group_id, category)
    
    if action == "inc":
        new_value = min(current + 5, 300)
    elif action == "dec":
        new_value = max(current - 5, 0)
    elif action == "set":
        if len(parts) < 6:
            await query.answer("خطأ", show_alert=True)
            return
        new_value = int(parts[5])
    else:
        return
    
    if new_value != current:
        await set_notification_delete_time(group_id, category, new_value)
        logging.info(f"Group {group_id} set delete time for {category} to {new_value}s")
    
    await query.answer(f"✅ {new_value}s")
    
    # Refresh view
    query.data = f"gs_deltime_{group_id}_{category}"
    await show_delete_timer(update, context)

# ==================== Register Handlers ====================

def register_group_settings_handlers(app):
    """Register group settings handlers."""
    
    # Settings command in groups
    app.add_handler(MessageHandler(
        filters.Regex(r"^الاعدادات$") & filters.ChatType.GROUPS,
        settings_command
    ))
    
    # Callback handlers for group settings (gs_ prefix)
    app.add_handler(CallbackQueryHandler(show_group_systems, pattern=r"^gs_systems_-?\d+$"))
    app.add_handler(CallbackQueryHandler(show_group_category_options, pattern=r"^gs_cat_-?\d+_"))
    app.add_handler(CallbackQueryHandler(toggle_group_category, pattern=r"^gs_toggle_-?\d+_"))
    app.add_handler(CallbackQueryHandler(back_to_group_settings, pattern=r"^gs_back_-?\d+$"))
    
    # Notifications handlers
    app.add_handler(CallbackQueryHandler(show_notifications_menu, pattern=r"^gs_notif_-?\d+_"))
    app.add_handler(CallbackQueryHandler(show_delete_timer, pattern=r"^gs_deltime_-?\d+_"))
    app.add_handler(CallbackQueryHandler(adjust_delete_timer, pattern=r"^gs_dt_"))
    
    logging.info("Group settings handlers registered.")
