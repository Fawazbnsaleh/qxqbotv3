import sys
import os
sys.path.append(os.path.abspath("al_rased"))
from core.utils.text import normalize_text

samples = [
    "يطلع سڪليف",   # Swash Kaf
    "اجازة مرضیة",  # Farsi Yeh
    "یا هلا",       # Farsi Yeh Start
    "گـروپ",        # Gaaf
    "چـا ت",        # Che
]

print("Verifying Normalization:")
for s in samples:
    print(f"'{s}' -> '{normalize_text(s)}'")
