import asyncio
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from core.database import get_group, save_topic, get_topic
from features.data_manager.manager import get_review_data
import logging

async def check_samples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow "check" or "فحص"
    text = update.message.text
    if text != "فحص":
        return

    # 1. Verify this is the review group
    review_group_id = await get_group("review")
    if not review_group_id or update.effective_chat.id != review_group_id:
        await update.message.reply_text("❌ هذا الأمر يعمل فقط في قروب المراجعة المعتمد.")
        return

    # 2. Load data
    data = get_review_data()
    if not data:
        await update.message.reply_text("❌ لم يتم العثور على ملف البيانات أو الملف فارغ.")
        return

    categories = data.get("categories", [])
    samples = data.get("samples", [])

    status_msg = await update.message.reply_text("⏳ جاري التحقق من الفئات وإنشاء المواضيع...")

    # 3. Create Topics for each category
    created_topics = 0
    for category in categories:
        # Check/Create Positive Topic
        pos_topic_id = await get_topic(category, "positive", review_group_id)
        if not pos_topic_id:
            try:
                topic = await context.bot.create_forum_topic(chat_id=review_group_id, name=f"{category} - Positive ✅")
                pos_topic_id = topic.message_thread_id
                await save_topic(category, "positive", pos_topic_id, review_group_id)
                created_topics += 1
            except Exception as e:
                logging.error(f"Failed to create topic {category}-Pos: {e}")

        # Check/Create Negative Topic
        neg_topic_id = await get_topic(category, "negative", review_group_id)
        if not neg_topic_id:
            try:
                topic = await context.bot.create_forum_topic(chat_id=review_group_id, name=f"{category} - Negative ❌")
                neg_topic_id = topic.message_thread_id
                await save_topic(category, "negative", neg_topic_id, review_group_id)
                created_topics += 1
            except Exception as e:
                logging.error(f"Failed to create topic {category}-Neg: {e}")
        
    await status_msg.edit_text(f"✅ تم الانتهاء من هيكلة المواضيع. (تم إنشاء {created_topics} موضوع جديد).\nجاري توزيع العينات...")

    # 4. Distribute samples
    sent_count = 0
    for sample in samples:
        category = sample.get("category")
        text_content = sample.get("text")
        
        # Determine target topic (logic: we send to 'positive' for review initially? 
        # Or maybe we send to a 'General' topic? 
        # The prompt says: "create topics... and create topics with violating samples and normal samples".
        # This implies we might ALREADY know the label or we just put them in 'Positive' topic as candidates?
        # Let's assume the JSON 'category' field implies the *suggested* category.
        # We will send it to the 'Positive' topic of that category so admins can confirm or delete.
        
        if category and text_content:
            target_topic_id = await get_topic(category, "positive", review_group_id)
            if target_topic_id:
                try:
                    await context.bot.send_message(
                        chat_id=review_group_id,
                        message_thread_id=target_topic_id,
                        text=f"🔍 عينة للمراجعة:\n\n{text_content}"
                    )
                    sent_count += 1
                    await asyncio.sleep(0.5) # Avoid flood limits
                except Exception as e:
                     logging.error(f"Failed to send sample: {e}")

    await context.bot.send_message(
        chat_id=review_group_id,
        text=f"✅ تمت عملية الفحص وتوزيع {sent_count} عينة."
    )

def register_review_handlers(app):
    app.add_handler(MessageHandler(filters.Regex(r"^فحص$"), check_samples))
