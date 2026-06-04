# Order matters — longest match first
CONSONANT_MAP = [
    # Aspirated clusters (2-char) — MUST come before single consonants
    ("bh", "BH"),
    ("dh", "DH"),
    ("gh", "GH"),
    ("kh", "KH"),
    ("ph", "F"),
    ("sh", "SH"),
    ("th", "TH"),
    ("ch", "CH"),
    ("jh", "JH"),
    # Retroflex (our custom notation)
    ("tt", "TT"),   # ट
    ("dd", "DD"),   # ड
    ("nn", "NN"),   # ण
    # Single consonants
    ("k", "K"), ("g", "G"), ("j", "J"),
    ("t", "T"), ("d", "D"), ("n", "N"),
    ("p", "P"), ("b", "B"), ("m", "M"),
    ("y", "Y"), ("r", "R"), ("l", "L"),
    ("v", "V"), ("w", "V"),   # v and w merge
    ("s", "S"), ("h", "H"),
    ("f", "F"), ("z", "Z"),
    ("q", "K"),               # q → K (Urdu loanwords)
    ("x", "KS"),
]

# Longest match first
VOWEL_MAP = [
    ("aa", "AA"), ("ee", "II"), ("oo", "UU"),
    ("ai", "AY"), ("ay", "AY"), ("ey", "AY"),
    ("au", "AW"), ("aw", "AW"), ("ou", "UU"),
    ("a",  "A"),  ("i",  "I"),  ("u",  "U"),
    ("e",  "E"),  ("o",  "O"),
]