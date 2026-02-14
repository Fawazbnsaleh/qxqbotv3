import re
import unicodedata

def normalize_text(text: str) -> str:
    if not text:
        return ""
    
    # 0. Normalize Arabic Presentation Forms to standard Arabic
    # This converts ﻋ -> ع, ﺟ -> ج, etc.
    text = unicodedata.normalize('NFKC', text)
    
    # --- Feature Tokenization (New) ---
    # 0. Replace Links (http, https, t.me, wa.me)
    text = re.sub(r'(https?://\S+|www\.\S+|t\.me/\S+|wa\.me/\S+)', ' __URL__ ', text)
    
    # 0. Replace Phone Numbers
    # Matches: +966..., 00966..., 05xxxxxxxx (SA format), and loose matches for numbers often used in these groups
    # We use a broad regex for numbers that look like contact info
    text = re.sub(r'(?:\+966|00966|966|05)\d{7,}', ' __PHONE__ ', text)
    
    # 0. Replace Mentions
    text = re.sub(r'@\w+', ' __MENTION__ ', text)
    
    # 0. De-spacing: Merge isolated Arabic letters (e.g. س ك ل ي ف -> سكليف)
    # Heuristic: Match a single Arabic letter followed by 1-3 spaces, repeatedly.
    # Note: We must be careful about "و" which is a valid single letter word (e.g. وكذا).
    # But usually "و" implies continuation. Merging "و" with next word "وكذا" -> "وكذا" is fine.
    # Pattern: Look for single char surrounded by boundaries or spaces.
    # A safer approach for "spaced spam": often 3+ letters.
    # Let's match sequences of 3+ (letter + space).
    def despacer(match):
        return match.group(0).replace(' ', '')
        
    # Regex: (ArabicChar + Space){2,} + ArabicChar
    # [\u0600-\u06FF] is broad range.
    text = re.sub(r'(?:[\u0600-\u06FF]\s+){2,}[\u0600-\u06FF]', despacer, text)
    # ----------------------------------

    # 1. Remove optional diacritics (Tashkeel)
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    
    # 2. Unify Alefs
    text = re.sub(r'[أإآ]', 'ا', text)
    
    # 3. Unify Taa Marbuta and Ha
    text = re.sub(r'ة', 'ه', text)
    
    # 4. Unify Yaa
    text = re.sub(r'ى', 'ي', text)
    
    # 5. Remove Tatweel (Kashida)
    text = re.sub(r'ـ+', '', text)
    
    # 5.1 Remove dots/dashes/invisible separators used to evade filters
    # Patterns like: س.ك.ل.ي.ف or س-ك-ل or س_ك_ل
    # Also remove zero-width characters
    text = re.sub(r'[\u200B-\u200D\u2060\uFEFF]', '', text)  # Zero-width chars
    text = re.sub(r'(?<=[\u0600-\u06FF])[.\-_~،,]+(?=[\u0600-\u06FF])', '', text)  # Separators between Arabic
    
    # 5.5 Homoglyph Normalization (Persian/Urdu chars to Arabic)
    # Swash Kaf -> Kaf, Farsi Yeh -> Yeh, etc.
    replacements = {
        'ڪ': 'ك', 'ك': 'ك', 'ک': 'ك', # Unify all Kafs
        'ی': 'ي', # Farsi Yeh
        'ھ': 'ه', # Heh
        'پ': 'ب',
        'چ': 'ج',
        'گ': 'ك',  # Persian Gaf → Kaf (visual similarity)
        'ڤ': 'ف'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # 6. Remove specific decorative characters
    text = re.sub(r'[\u0332\u0305\u00B8]', '', text) 
    
    # 7. Normalize repeated characters
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    
    # 8. Lowercase (for the tokens we just added and English words)
    text = text.lower()
    
    return text.strip()

# Test
if __name__ == "__main__":
    samples = [
        "ســــكــــلــــيــــف",
        "تواصل ت.me/abc أو wa.me/966500000000",
        "اتصل 0555555555",
        "رواااااتب",
        "ت̲̅ق̲̅ر̲̅ي̲̅ر̲̅"
    ]
    for s in samples:
        print(f"Original: {s} -> Normalized: {normalize_text(s)}")
