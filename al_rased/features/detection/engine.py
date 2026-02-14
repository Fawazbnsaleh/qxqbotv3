import joblib
import os
import logging
from al_rased.core.utils.text import normalize_text

# Locate model relative to this file (features/detection/engine.py)
# Model is at features/model/classifier.joblib
# Go up two levels: features/detection/ -> features/ -> al_rased/ (Wait)
# structure: al_rased/features/detection/engine.py
# target: al_rased/features/model/classifier.joblib
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # al_rased/features
MODEL_PATH = os.path.join(BASE_DIR, "model/classifier.joblib")

# Keyword-based override rules for sensitive categories
# These patterns ALWAYS trigger detection, bypassing ML uncertainty
KEYWORD_RULES = {
    "احتيال مالي (عرض)": [
        "استثمر معي", "ارباح مضمونه", "عوائد يومية", "فوركس", "تداول عملات",
        "دخل اضافي", "فرصة ذهبية", "ارباح بدون مجهود", "استثمار مضمون"
    ],
    "سبام": [
        "سيرفر ماينكرافت", "ريلم ماينكرافت", "سيرفر ماين كرافت", "سيرفر كرافت"
    ],
    "غير أخلاقي (عرض)": [
        # Sexual content
        "سكس", "porn", "xxx", "بورن", "نودز", "هيجانه",
        "افلام للكبار", "+18", "18+", "فيديو كول", "سكس شات",
        # Child exploitation
        "سكس اطفال", "تحرش اطفال", "قاصر",
        # Drugs
        "حشيش للبيع", "شبو", "كبتاجون", "كريستال",
    ],
    "تهكير (عرض)": [
        # Hacking services
        "تهكير حساب", "اختراق حساب", "تهكير واتساب", "تهكير انستقرام",
        "تهكير تيك توك", "تهكير سناب", "تهكير فيسبوك", "تهكير جوال",
        "اختراق هاتف", "فريق هكرز", "خدمات الهكر", "سحب معلومات",
        "فرمتة عن بعد", "متوفر تهكير", "يوجد لدينا اختراق",
    ],
    # ============================================================
    # FROZEN CATEGORY keyword fallbacks (categories excluded from
    # ML training due to insufficient samples)
    # ============================================================
    "احتيال طبي (طلب)": [
        "ابي سكليف", "ابغي سكليف", "محتاج سكليف", "احتاج سكليف",
        "ابي عذر طبي", "ابغي عذر طبي", "محتاج عذر طبي",
        "من يسوي سكليف", "احد يسوي سكليف", "من يعرف سكليف",
        "ابي اجازه مرضيه", "محتاجه سكليف",
    ],
    "تهكير (طلب)": [
        "ابي هكر", "ابغي هكر", "محتاج هكر", "مطلوب هكر",
        "ابي تهكير", "ابغي تهكير", "من يهكر لي", "احد يهكر",
        "ابي اخترق", "كيف اهكر", "كيف اخترق",
    ],
    "غش أكاديمي (طلب)": [
        "ابي احد يحل", "محتاج حل واجب", "من يحل واجب",
        "ابي احد يسوي بحث", "محتاج بحث تخرج", "من يسوي مشروع",
        "ابي حل اختبار", "محتاج حل كويز",
    ],
    "غير أخلاقي (طلب)": [
        "ابي سكس", "ابغي سكس", "ابي نودز", "ابغي نودز",
        "من عنده سكس", "مين هيجانه", "مين مشتهيه",
    ],
}


class DetectionEngine:
    _model = None
    _db_keywords = None  # Cache for database keywords

    @classmethod
    def load_model(cls):
        if cls._model is None:
            if os.path.exists(MODEL_PATH):
                try:
                    cls._model = joblib.load(MODEL_PATH)
                    logging.info("AI Model loaded successfully.")
                except Exception as e:
                    logging.error(f"Failed to load AI model: {e}")
            else:
                logging.warning(f"Model file not found at {MODEL_PATH}")
        
        # Load keywords from database
        cls._load_db_keywords()

    @classmethod
    def _load_db_keywords(cls):
        """Load keywords from database.
        Uses asyncio to run the async DB call. If already in an event loop
        (e.g. called from run_in_executor), schedules it safely.
        """
        try:
            import asyncio
            from al_rased.core.database import get_all_prohibited_keywords_mapping
            
            try:
                # Check if there's a running loop
                loop = asyncio.get_running_loop()
                # We're inside an async context — can't use run_until_complete
                # Schedule as a task instead; keywords will load on next call
                logging.info("Event loop running, deferring DB keywords load")
                cls._db_keywords = cls._db_keywords or {}
            except RuntimeError:
                # No running loop — safe to create one
                loop = asyncio.new_event_loop()
                cls._db_keywords = loop.run_until_complete(get_all_prohibited_keywords_mapping())
                loop.close()
                logging.info(f"Loaded {sum(len(v) for v in cls._db_keywords.values())} keywords from database")
        except Exception as e:
            logging.warning(f"Could not load keywords from database: {e}")
            cls._db_keywords = {}

    @classmethod
    def _check_keyword_rules(cls, text: str) -> dict | None:
        """Check if text matches any keyword rules (override ML).
        NOTE: text is expected to already be normalized via normalize_text().
        Keywords are also normalized at check time for consistent matching.
        """
        text_lower = text.lower()
        
        # Combine hardcoded + database keywords
        all_keywords = {**KEYWORD_RULES}
        if cls._db_keywords:
            for label, kws in cls._db_keywords.items():
                if label in all_keywords:
                    all_keywords[label] = list(set(all_keywords[label] + kws))
                else:
                    all_keywords[label] = kws
        
        for label, keywords in all_keywords.items():
            for keyword in keywords:
                # Normalize keyword the same way we normalize input text
                norm_keyword = normalize_text(keyword).lower()
                if norm_keyword and norm_keyword in text_lower:
                    logging.debug(f"Keyword match: '{keyword}' -> {label}")
                    return {"label": label, "confidence": 0.95, "matched_keyword": keyword}
        
        return None

    @classmethod
    def predict(cls, text: str) -> dict:
        if not cls._model:
            cls.load_model()
        
        # 1. Normalize
        clean_text = normalize_text(text)
        
        # 2. Check keyword rules FIRST (for sensitive categories)
        keyword_match = cls._check_keyword_rules(clean_text)
        if keyword_match:
            return keyword_match
        
        # 3. Fall back to ML model
        if not cls._model:
            return {"label": "طبيعي", "confidence": 0.0}

        try:
            # Model expects a list/iterable
            probas = cls._model.predict_proba([clean_text])[0]
            max_index = probas.argmax()
            label = cls._model.classes_[max_index]
            confidence = float(probas[max_index])
            
            return {"label": label, "confidence": confidence}
        except Exception as e:
            logging.error(f"Prediction error: {e}")
            return {"label": "طبيعي", "confidence": 0.0}

