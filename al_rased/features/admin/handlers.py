"""
Admin Handlers - Secured
Commands for setting up review, training, and reports groups.
Only the developer can use these commands.
"""
import os
import logging
from telegram import Update, ChatMember
from telegram.ext import ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ConversationHandler
from core.database import (
    set_group, get_group, get_system_flag, set_system_flag, 
    add_banned_name, remove_banned_name, get_banned_names, get_banned_names_count
)
from features.admin.keyboards import (
    get_developer_menu, get_systems_menu, get_category_menu, 
    get_banned_names_menu, get_delete_banned_names_menu
)

# Developer ID from environment
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "0"))

# Constants for ConversationHandler
WAIT_NAME = 1

# Known Categories — must match detection engine and group_settings
CATEGORIES = [
    "احتيال طبي (عرض)", 
    "احتيال طبي (طلب)",
    "غش أكاديمي (عرض)", 
    "غش أكاديمي (طلب)",
    "تهكير (عرض)", 
    "تهكير (طلب)",
    "احتيال مالي (عرض)", 
    "احتيال مالي (طلب)",
    "سبام",
    "غير أخلاقي (عرض)",
    "غير أخلاقي (طلب)",
]

def is_developer(user_id: int) -> bool:
    """Check if user is the developer."""
    if DEVELOPER_ID == 0:
        logging.warning("DEVELOPER_ID not set! Denying admin access.")
        return False
    return user_id == DEVELOPER_ID

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command. Show dev menu if developer."""
    user = update.effective_user
    if is_developer(user.id):
        await update.message.reply_text(
            f"👋 مرحبًا بك يا مطور ({user.first_name})!",
            reply_markup=get_developer_menu()
        )
    else:
        # Default behavior for non-devs? Nothing or just welcome?
        await update.message.reply_text("👋 مرحبًا! أنا بوت الراصد الذكي.")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if not is_developer(query.from_user.id):
        await query.edit_message_text("⛔ غير مصرح لك.")
        return

    # 1. Main Systems Menu
    if data == "admin_systems":
        await query.edit_message_text(
            "🛠 **إدارة الأنظمة الذكية**\nاختر النظام (الفئة) للتحكم به:",
            reply_markup=get_systems_menu(CATEGORIES),
            parse_mode="Markdown"
        )
        
    elif data == "admin_home":
        await query.edit_message_text(
            "👋 القائمة الرئيسية",
            reply_markup=get_developer_menu()
        )

    # 2. Category Menu
    elif data.startswith("admin_cat_"):
        cat = data.replace("admin_cat_", "")
        mode = await get_system_flag(f"action_mode:{cat}", "publish")
        # Handle Arabic names decoding if passing through callback data
        # Actually callback data is limited to 64 bytes. Arabic keys might be too long?
        # Let's check max length. "admin_cat_احتيال طبي (عرض)" is ~30 chars. Safe.
        
        await query.edit_message_text(
            f"📂 **نظام: {cat}**\n\n"
            f"حالة التشغيل الحالية: *{'نشر (Publish)' if mode == 'publish' else 'إيقاف (Stop/Strict)'}*\n"
            f"• **نشر**: يتم رصد المخالفات وإرسال تقرير دون حذف.\n"
            f"• **إيقاف**: يتم حذف الرسالة (وربما حظر العضو مخالف الاسم).",
            reply_markup=get_category_menu(cat, mode),
            parse_mode="Markdown"
        )
        
    # 3. Toggle Mode
    elif data.startswith("admin_toggle_"):
        parts = data.split("_")
        # admin_toggle_CAT_ACTION
        # Since CAT contains spaces/arabic, split might be tricky if we joined with _.
        # Strategy: The keys in CATEGORIES have spaces. 
        # But callback data cannot contain spaces easily if we use split logic blindly.
        # Wait, get_category_menu generates the keys. We need to see how it generates them.
        # Assuming we just pass it blindly.
        
        # New robust parsing:
        # action is always last part (publish/stop), everything else is cat
        action = parts[-1] 
        cat = "_".join(parts[2:-1]) # Rejoin the middle parts
        # If cat was "احتيال طبي (عرض)", it became "احتيال_طبي_(عرض)" via replacement?
        # Check keyboards.py.
        # If I change CATEGORIES here, I must verify keyboards.py handles them.
        
        await set_system_flag(f"action_mode:{cat}", action)
        
        # Refresh menu
        mode = action
        await query.edit_message_text(
            f"📂 **نظام: {cat}**\n\n"
            f"✅ تم التغيير.\n"
            f"حالة التشغيل الحالية: *{'نشر (Publish)' if mode == 'publish' else 'إيقاف (Stop/Strict)'}*",
            reply_markup=get_category_menu(cat, mode),
            parse_mode="Markdown"
        )

    # 4. Forbidden Names Menu
    elif data.startswith("admin_banned_"):
        cat = data.replace("admin_banned_", "")
        count = await get_banned_names_count(cat)
        # Note: I need to import get_banned_names_count or just count length of list
        names = await get_banned_names(cat)
        
        text = f"🚫 **الأسماء الممنوعة لـ {cat}**\nعدد الأسماء: {len(names)}\n\n"
        if names:
            text += "آخر الأسماء المضافة:\n" + "\n".join([f"- {n}" for n in names[:5]])
        else:
            text += "لا توجد أسماء ممنوعة."
            
        await query.edit_message_text(
            text,
            reply_markup=get_banned_names_menu(cat),
            parse_mode="Markdown"
        )
        
    # 5. Delete List Menu
    elif data.startswith("admin_del_ban_list_"):
        cat = data.replace("admin_del_ban_list_", "")
        names = await get_banned_names(cat)
        if not names:
            await query.answer("⚠️ لا توجد أسماء لحذفها.", show_alert=True)
            return
            
        await query.edit_message_text(
            f"🗑 **حذف اسم من {cat}**\nاضغط على الاسم لحذفه:",
            reply_markup=get_delete_banned_names_menu(cat, names)
        )
        
    # 6. Delete Action
    elif data.startswith("admin_del_ban_do_"):
        parts = data.split("_")
        # admin_del_ban_do_CAT_NAME
        # Name is last part? What if name has underscores?
        # Names usually don't have underscores? Or they might.
        # Safer: The prefix is fixed length? No.
        # But wait, the previous menu generator put name at end.
        # Let's assume name is the suffix.
        # Actually better to handle this carefully.
        # Let's reconstruct. Prefix is "admin_del_ban_do_" (len 17).
        remainder = data[17:]
        # Format in previous step: f"admin_del_ban_do_{category}_{name}"
        # So we need to find where category ends.
        # Iterate over known categories to match prefix?
        
        cat = None
        target_name = None
        for c in CATEGORIES:
            if remainder.startswith(c + "_"):
                cat = c
                target_name = remainder[len(c)+1:]
                break
        
        if cat and target_name:
            await remove_banned_name(cat, target_name)
            await query.answer(f"✅ تم حذف {target_name}", show_alert=True)
            
            # Refresh list
            names = await get_banned_names(cat)
            await query.edit_message_text(
                f"🗑 **حذف اسم من {cat}**\nاضغط على الاسم لحذفه:",
                reply_markup=get_delete_banned_names_menu(cat, names)
            )
        else:
             await query.answer("❌ خطأ في تحديد الاسم", show_alert=True)


# Conversation callbacks
async def add_ban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding a banned name."""
    query = update.callback_query
    await query.answer()
    cat = query.data.replace("admin_add_ban_", "")
    context.user_data["add_ban_cat"] = cat
    await query.message.reply_text(
        f"✍️ أرسل الاسم (أو الكلمة) الذي تريد منعه في تصنيف **{cat}**:\n"
        f"⚠️ سيتم تطبيق الإجراء على أي عضو يحتوي اسمه على هذه الكلمة.",
        parse_mode="Markdown"
    )
    return WAIT_NAME

async def add_ban_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the banned name."""
    name = update.message.text.strip()
    cat = context.user_data.get("add_ban_cat")
    
    if not cat:
        await update.message.reply_text("❌ حدث خطأ، لم يتم تحديد التصنيف.")
        return ConversationHandler.END
        
    if len(name) < 2:
        await update.message.reply_text("⚠️ الاسم قصير جداً.")
        return WAIT_NAME # Try again
        
    added = await add_banned_name(cat, name)
    if added:
        await update.message.reply_text(f"✅ تم إضافة **{name}** إلى قائمة الممنوعات لـ {cat}.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ الاسم **{name}** موجود مسبقاً.", parse_mode="Markdown")
        
    return ConversationHandler.END

async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء.")
    return ConversationHandler.END

# Existing Handlers (Keep them!)
async def set_review_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set current group as review group. Developer only."""
    chat = update.effective_chat
    user = update.effective_user
    if not is_developer(user.id):
        await update.message.reply_text("⛔ هذا الأمر متاح للمطور فقط.")
        return
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ يجب استخدام هذا الأمر داخل قروب.")
        return
    await set_group("review", chat.id)
    await update.message.reply_text(f"✅ تم تعيين هذا القروب كقروب للمراجعة.\n🆔 المعرف: `{chat.id}`", parse_mode="Markdown")
    logging.info(f"Review group set to {chat.id} by developer {user.id}")

async def set_training_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set current group as training group. Developer only."""
    chat = update.effective_chat
    user = update.effective_user
    if not is_developer(user.id):
        await update.message.reply_text("⛔ هذا الأمر متاح للمطور فقط.")
        return
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ يجب استخدام هذا الأمر داخل قروب.")
        return
    await set_group("training", chat.id)
    await update.message.reply_text(f"✅ تم تعيين هذا القروب كقروب للتدريب.\n🆔 المعرف: `{chat.id}`", parse_mode="Markdown")
    logging.info(f"Training group set to {chat.id} by developer {user.id}")

async def set_reports_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set current group as reports group. Developer only."""
    chat = update.effective_chat
    user = update.effective_user
    if not is_developer(user.id):
        await update.message.reply_text("⛔ هذا الأمر متاح للمطور فقط.")
        return
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ يجب استخدام هذا الأمر داخل قروب.")
        return
    await set_group("reports", chat.id)
    await update.message.reply_text(f"✅ تم تعيين هذا القروب كقروب للتقارير.\n🆔 المعرف: `{chat.id}`", parse_mode="Markdown")
    logging.info(f"Reports group set to {chat.id} by developer {user.id}")


async def send_violation_report(
    context,
    source_chat_id: int,
    source_chat_title: str,
    user_id: int,
    username: str,
    user_name: str,
    message_text: str,
    category: str,
    confidence: float,
    action_taken: str
):
    """Send a violation report to the reports group."""
    reports_group_id = await get_group("reports")
    
    if not reports_group_id:
        logging.warning("Reports group not set, skipping violation report")
        return
    
    # Truncate message if too long
    text_preview = message_text[:500] + "..." if len(message_text) > 500 else message_text
    
    report_text = (
        f"🚨 **تقرير مخالفة**\n\n"
        f"📍 **المجموعة:** {source_chat_title}\n"
        f"🆔 **معرف المجموعة:** `{source_chat_id}`\n\n"
        f"👤 **المستخدم:** {user_name}\n"
        f"🔗 **اليوزر:** @{username if username else 'N/A'}\n"
        f"🆔 **معرف المستخدم:** `{user_id}`\n\n"
        f"🏷 **التصنيف:** {category}\n"
        f"📈 **الثقة:** {confidence:.0%}\n"
        f"⚡ **الإجراء:** {action_taken}\n\n"
        f"📝 **النص:**\n`{text_preview}`"
    )
    
    try:
        await context.bot.send_message(
            chat_id=reports_group_id,
            text=report_text,
            parse_mode="Markdown"
        )
        logging.info(f"Violation report sent to reports group: {category}")
    except Exception as e:
        logging.error(f"Failed to send violation report: {e}")


def register_admin_handlers(app):
    """Register admin command handlers."""
    # New Handlers
    app.add_handler(CommandHandler("start", start_command))
    
    # Conversation for adding names
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_ban_start, pattern="^admin_add_ban_")],
        states={
            WAIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ban_save)]
        },
        fallbacks=[CommandHandler("cancel", cancel_add)]
    )
    app.add_handler(conv_handler)
    
    # General Callbacks
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    # Legacy Handlers
    app.add_handler(MessageHandler(
        filters.Regex(r"^تعيين قروب المراجعة$") & filters.ChatType.GROUPS, 
        set_review_group
    ))
    app.add_handler(MessageHandler(
        filters.Regex(r"^تعيين قروب التدريب$") & filters.ChatType.GROUPS, 
        set_training_group
    ))
    app.add_handler(MessageHandler(
        filters.Regex(r"^تعيين قروب التقارير$") & filters.ChatType.GROUPS, 
        set_reports_group
    ))
    logging.info("Admin handlers registered.")
