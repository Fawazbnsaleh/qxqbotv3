import sys
import os
sys.path.append(os.path.abspath("al_rased"))
from core.utils.text import normalize_text

# Test Arabic Presentation Forms (U+FB50-U+FDFF, U+FE70-U+FEFF)
samples = [
    "ﻋندها اﻋذار",  # Presentation forms
    "ﺟﺎﻣﻌﻪ",       # Presentation forms
    "ﺳﻜﻠﻴﻒ",       # Presentation forms
    "عندها اعذار", # Standard Arabic (for comparison)
]

print("Testing Arabic Presentation Forms Normalization:")
print("=" * 50)
for s in samples:
    normalized = normalize_text(s)
    print(f"Original:   '{s}'")
    print(f"Normalized: '{normalized}'")
    print("-" * 30)
