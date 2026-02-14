"""
Activation System Handlers
Manages bot activation in groups, thresholds, and VIP settings.
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember, ChatMemberUpdated
from telegram.ext import (
    ContextTypes, 
    CallbackQueryHandler,
    ChatMemberHandler
)
from core.database import (
    get_activation_threshold,
    set_activation_threshold,
    add_managed_group,
    get_managed_group,
    set_group_vip,
    set_group_active,
    remove_managed_group
)

# Developer ID from environment
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "0"))

def is_developer(user_id: int) -> bool:
    """Check if user is the developer."""
    if DEVELOPER_ID == 0:
        return False
    return user_id == DEVELOPER_ID

async def check_developer_access(update: Update) -> bool:
    """Check developer access for callback queries."""
    user_id = update.effective_user.id
    if not is_developer(user_id):
        if update.callback_query:
            await update.callback_query.answer("⛔ غير مصرح لك", show_alert=True)
        return False
    return True

# ==================== Activation Menu ====================

async def show_activation_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show activation system menu."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    threshold = await get_activation_threshold()
    
    text = f"""
⚡ **نظام التفعيل**

يتحكم هذا النظام في كيفية تفعيل البوت في القروبات الجديدة.

📊 **الإعدادات الحالية:**
• حد التفعيل: **{threshold}** أعضاء

💡 **كيف يعمل:**
عندما يُضاف البوت لقروب جديد:
1. يفحص عدد الأعضاء والصلاحيات
2. إذا كان العدد أقل من الحد → يغادر مع رسالة
3. إذا نجح → يُرسل تقرير للمطور
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 حد التفعيل", callback_data="act_threshold")],
        [InlineKeyboardButton("📋 القروبات المفعلة", callback_data="act_groups")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Threshold Settings ====================

async def show_threshold_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show threshold settings with +/- buttons."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    threshold = await get_activation_threshold()
    
    text = f"""
📊 **حد التفعيل**

الحد الأدنى لعدد الأعضاء المطلوب لتفعيل البوت في القروب.

**الحد الحالي:** {threshold} أعضاء

استخدم الأزرار أدناه للتعديل:
"""
    
    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data="act_th_dec"),
            InlineKeyboardButton(f"  {threshold}  ", callback_data="act_th_current"),
            InlineKeyboardButton("➕", callback_data="act_th_inc")
        ],
        [
            InlineKeyboardButton("1️⃣", callback_data="act_th_set_1"),
            InlineKeyboardButton("3️⃣", callback_data="act_th_set_3"),
            InlineKeyboardButton("5️⃣", callback_data="act_th_set_5"),
            InlineKeyboardButton("🔟", callback_data="act_th_set_10")
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data="activation_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def adjust_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle threshold adjustment buttons."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    action = query.data
    
    current = await get_activation_threshold()
    
    if action == "act_th_inc":
        new_value = min(current + 1, 100)
    elif action == "act_th_dec":
        new_value = max(current - 1, 1)
    elif action.startswith("act_th_set_"):
        new_value = int(action.replace("act_th_set_", ""))
    elif action == "act_th_current":
        await query.answer(f"الحد الحالي: {current}", show_alert=False)
        return
    else:
        return
    
    if new_value != current:
        await set_activation_threshold(new_value)
        logging.info(f"Developer changed activation threshold to {new_value}")
        await query.answer(f"✅ تم التعديل: {new_value}", show_alert=False)
    
    # Refresh the view
    await show_threshold_settings(update, context)

# ==================== Managed Groups List ====================

async def show_managed_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of managed groups."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    from core.database import get_all_managed_groups
    groups = await get_all_managed_groups()
    
    if not groups:
        text = """
📋 **القروبات المفعلة**

لا توجد قروبات مسجلة بعد.
سيظهر هنا القروبات التي يتم تفعيل البوت فيها.
"""
    else:
        text = f"""
📋 **القروبات المفعلة** ({len(groups)})

"""
        for g in groups[:10]:
            status = "⭐" if g["is_vip"] else ("✅" if g["is_active"] else "❌")
            text += f"{status} {g['title'][:25]} ({g['member_count']} عضو)\n"
        
        if len(groups) > 10:
            text += f"\n... و {len(groups) - 10} قروبات أخرى"
    
    keyboard = [
        [InlineKeyboardButton("🔙 رجوع", callback_data="activation_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== Group Control Buttons ====================

async def handle_group_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle VIP/Disable/Invite buttons from group notifications."""
    if not await check_developer_access(update):
        return
    
    query = update.callback_query
    data = query.data
    
    # Parse: grp_action_groupid
    parts = data.split("_", 2)
    if len(parts) < 3:
        await query.answer("خطأ", show_alert=True)
        return
    
    action = parts[1]
    try:
        group_id = int(parts[2])
    except ValueError:
        await query.answer("خطأ في البيانات", show_alert=True)
        return
    
    if action == "vip":
        await set_group_vip(group_id, True)
        await query.answer("⭐ تم تفعيل VIP", show_alert=True)
        logging.info(f"Group {group_id} set as VIP")
        
    elif action == "disable":
        await set_group_active(group_id, False)
        await query.answer("❌ تم التعطيل", show_alert=True)
        logging.info(f"Group {group_id} disabled")
        
    elif action == "enable":
        await set_group_active(group_id, True)
        await query.answer("✅ تم التفعيل", show_alert=True)
        logging.info(f"Group {group_id} enabled")
        
    elif action == "invite":
        try:
            invite = await context.bot.create_chat_invite_link(group_id)
            await query.answer()
            await query.message.reply_text(f"🔗 رابط الدعوة:\n{invite.invite_link}")
        except Exception as e:
            await query.answer(f"❌ فشل: {str(e)[:50]}", show_alert=True)
    
    # Update message buttons
    group = await get_managed_group(group_id)
    if group:
        await update_group_notification_buttons(query.message, group)

async def update_group_notification_buttons(message, group: dict):
    """Update the inline buttons on a group notification message."""
    group_id = group["group_id"]
    is_vip = group.get("is_vip", False)
    is_active = group.get("is_active", True)
    
    keyboard = []
    
    if not is_vip:
        keyboard.append([InlineKeyboardButton("⭐ تفعيل VIP", callback_data=f"grp_vip_{group_id}")])
    
    if is_active:
        keyboard.append([InlineKeyboardButton("❌ تعطيل", callback_data=f"grp_disable_{group_id}")])
    else:
        keyboard.append([InlineKeyboardButton("✅ تفعيل", callback_data=f"grp_enable_{group_id}")])
    
    keyboard.append([InlineKeyboardButton("🔗 إنشاء رابط دعوة", callback_data=f"grp_invite_{group_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await message.edit_reply_markup(reply_markup=reply_markup)
    except Exception:
        pass  # Message might be too old

# ==================== Bot Added to Group Handler ====================

def extract_status_change(chat_member_update: ChatMemberUpdated):
    """Extract status change from ChatMemberUpdated."""
    status_change = chat_member_update.difference().get("status")
    old_is_member = chat_member_update.old_chat_member.status in [
        ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER
    ]
    new_is_member = chat_member_update.new_chat_member.status in [
        ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER
    ]
    return old_is_member, new_is_member

async def on_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is added to a new group."""
    my_chat_member = update.my_chat_member
    
    # Check if this is about the bot itself
    if my_chat_member.new_chat_member.user.id != context.bot.id:
        return
    
    old_is_member, new_is_member = extract_status_change(my_chat_member)
    
    # Bot was added to group
    if not old_is_member and new_is_member:
        chat = my_chat_member.chat
        added_by = my_chat_member.from_user
        
        logging.info(f"Bot added to group: {chat.title} ({chat.id}) by {added_by.id}")
        
        await process_new_group(chat, added_by, context)
    
    # Bot was removed from group
    elif old_is_member and not new_is_member:
        chat = my_chat_member.chat
        logging.info(f"Bot removed from group: {chat.title} ({chat.id})")
        await remove_managed_group(chat.id)

async def process_new_group(chat, added_by, context: ContextTypes.DEFAULT_TYPE):
    """Process a new group the bot was added to."""
    
    # Get group info
    try:
        member_count = await context.bot.get_chat_member_count(chat.id)
    except Exception as e:
        member_count = 0
        logging.error(f"Failed to get member count: {e}")
    
    # Get threshold
    threshold = await get_activation_threshold()
    
    # Check member count
    if member_count < threshold:
        # Not enough members - leave
        fail_reason = f"عدد الأعضاء ({member_count}) أقل من الحد المطلوب ({threshold})"
        
        # Send message to group
        try:
            await context.bot.send_message(
                chat.id,
                f"⚠️ **عذراً، لا يمكن تفعيل البوت**\n\n"
                f"السبب: {fail_reason}\n\n"
                f"يتطلب البوت على الأقل **{threshold}** أعضاء للعمل.\n"
                f"سيتم مغادرة القروب تلقائياً.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Failed to send leave message: {e}")
        
        # Leave group
        try:
            await context.bot.leave_chat(chat.id)
        except Exception as e:
            logging.error(f"Failed to leave chat: {e}")
        
        # Notify developer
        if DEVELOPER_ID:
            await context.bot.send_message(
                DEVELOPER_ID,
                f"❌ **فشل تفعيل البوت**\n\n"
                f"📍 القروب: {chat.title}\n"
                f"🆔 المعرف: `{chat.id}`\n"
                f"👤 أضافه: {added_by.first_name} (`{added_by.id}`)\n"
                f"👥 الأعضاء: {member_count}\n\n"
                f"**السبب:** {fail_reason}",
                parse_mode="Markdown"
            )
        return
    
    # Check bot permissions
    try:
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        is_admin = bot_member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        
        # Check specific permissions
        can_delete = getattr(bot_member, 'can_delete_messages', False)
        can_restrict = getattr(bot_member, 'can_restrict_members', False)
        
        permissions_ok = is_admin and can_delete and can_restrict
        
        if not permissions_ok:
            missing = []
            if not is_admin:
                missing.append("صلاحية المشرف")
            if not can_delete:
                missing.append("حذف الرسائل")
            if not can_restrict:
                missing.append("تقييد الأعضاء")
            
            permissions_text = "، ".join(missing)
            fail_reason = f"صلاحيات ناقصة: {permissions_text}"
        else:
            fail_reason = None
            
    except Exception as e:
        fail_reason = f"خطأ في فحص الصلاحيات: {str(e)[:50]}"
        permissions_ok = False
    
    if fail_reason:
        # Missing permissions - leave
        try:
            await context.bot.send_message(
                chat.id,
                f"⚠️ **لا يمكن تفعيل البوت**\n\n"
                f"السبب: {fail_reason}\n\n"
                f"يرجى إعطاء البوت صلاحيات المشرف مع:\n"
                f"• حذف الرسائل\n"
                f"• تقييد الأعضاء\n\n"
                f"سيتم مغادرة القروب.",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        
        try:
            await context.bot.leave_chat(chat.id)
        except Exception:
            pass
        
        # Notify developer
        if DEVELOPER_ID:
            await context.bot.send_message(
                DEVELOPER_ID,
                f"❌ **فشل تفعيل البوت**\n\n"
                f"📍 القروب: {chat.title}\n"
                f"🆔 المعرف: `{chat.id}`\n"
                f"👤 أضافه: {added_by.first_name} (`{added_by.id}`)\n"
                f"👥 الأعضاء: {member_count}\n\n"
                f"**السبب:** {fail_reason}",
                parse_mode="Markdown"
            )
        return
    
    # Success! Register group
    await add_managed_group(chat.id, chat.title, member_count, added_by.id)
    
    # Send success message to group
    try:
        await context.bot.send_message(
            chat.id,
            f"✅ **تم تفعيل البوت بنجاح!**\n\n"
            f"مرحباً! أنا بوت الراصد للكشف الذكي عن المخالفات.\n\n"
            f"📋 للإعدادات، يمكن للمشرفين إرسال: `الاعدادات`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Failed to send success message: {e}")
    
    # Notify developer with control buttons
    if DEVELOPER_ID:
        keyboard = [
            [InlineKeyboardButton("⭐ تفعيل VIP", callback_data=f"grp_vip_{chat.id}")],
            [InlineKeyboardButton("❌ تعطيل", callback_data=f"grp_disable_{chat.id}")],
            [InlineKeyboardButton("🔗 إنشاء رابط دعوة", callback_data=f"grp_invite_{chat.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            DEVELOPER_ID,
            f"✅ **تم تفعيل البوت بنجاح!**\n\n"
            f"📍 القروب: {chat.title}\n"
            f"🆔 المعرف: `{chat.id}`\n"
            f"👤 أضافه: {added_by.first_name} (`{added_by.id}`)\n"
            f"👥 الأعضاء: {member_count}\n"
            f"🔐 الصلاحيات: ✅ كاملة",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    logging.info(f"Successfully activated in group: {chat.title} ({chat.id})")

# ==================== Register Handlers ====================

def register_activation_handlers(app):
    """Register activation system handlers."""
    
    # Menu handlers
    app.add_handler(CallbackQueryHandler(show_activation_menu, pattern="^activation_menu$"))
    app.add_handler(CallbackQueryHandler(show_threshold_settings, pattern="^act_threshold$"))
    app.add_handler(CallbackQueryHandler(adjust_threshold, pattern="^act_th_"))
    app.add_handler(CallbackQueryHandler(show_managed_groups, pattern="^act_groups$"))
    
    # Group control handlers
    app.add_handler(CallbackQueryHandler(handle_group_control, pattern="^grp_"))
    
    # Bot added/removed from groups
    app.add_handler(ChatMemberHandler(on_bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))
    
    logging.info("Activation system handlers registered.")
