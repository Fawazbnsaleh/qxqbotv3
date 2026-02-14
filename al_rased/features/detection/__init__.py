from .handlers import register_detection_handlers

def register_feature(app):
    register_detection_handlers(app)
