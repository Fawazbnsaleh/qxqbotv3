import os
import logging
from telegram.ext import ApplicationBuilder, Application
from .database import init_db
from .cache import cache

# Import feature handlers (to be implemented)
from features.admin import register_admin_handlers
from features.review_flow import register_review_handlers
from features.detection import register_feature as register_detection_handlers
from features.developer import register_developer_handlers
from features.group_settings import register_group_settings_handlers
from features.activation import register_activation_handlers

async def post_init(application: Application):
    await init_db()
    await cache.connect()
    logging.info("Bot components initialized.")

async def post_shutdown(application: Application):
    await cache.close()
    logging.info("Bot components shut down.")

def create_app() -> Application:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is not set.")

    app = ApplicationBuilder().token(token).post_init(post_init).post_shutdown(post_shutdown).build()

    # Register handlers here
    register_developer_handlers(app)  # Developer menu first (priority)
    register_activation_handlers(app)  # Activation system
    register_group_settings_handlers(app)  # Group settings
    register_admin_handlers(app)
    register_review_handlers(app)
    register_detection_handlers(app)
    
    return app
