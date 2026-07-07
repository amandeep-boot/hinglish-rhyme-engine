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

# ARPAbet (CMUdict) -> unified token space.
#
# The English path (encoder/english.py) looks a word up in CMUdict, which returns
# ARPAbet phonemes, and rewrites them into the SAME token vocabulary the Hindi path
# emits. Keeping the symbols identical (see VOWELS in encoder.py) is what lets a
# Hindi and an English word land in the same rhyme bucket, e.g. pyaar / car -> AA-R.
#
# Vowel choices are deliberately lossy: ARPAbet has more vowel distinctions than the
# Hindi token set, so several ARPAbet vowels collapse onto the nearest Hindi vowel.
# A couple of phonemes carry a trailing consonantal sound and expand to two tokens
# (ER -> A R, OY -> O Y) so the final consonant still counts toward the rhyme.
ARPABET_MAP: dict[str, list[str]] = {
    # Vowels
    "AA": ["AA"],  # father, car
    "AE": ["A"],   # cat
    "AH": ["A"],   # but, sofa (schwa)
    "AO": ["O"],   # war, law
    "AW": ["AW"],  # cow
    "AY": ["AY"],  # hide
    "EH": ["E"],   # bed
    "ER": ["A", "R"],  # bird, her (rhotic vowel)
    "EY": ["E"],   # say
    "IH": ["I"],   # sit
    "IY": ["II"],  # see
    "OW": ["O"],   # go
    "OY": ["O", "Y"],  # boy
    "UH": ["U"],   # book
    "UW": ["UU"],  # too
    # Consonants
    "B": ["B"],   "CH": ["CH"], "D": ["D"],  "DH": ["D"],  "F": ["F"],
    "G": ["G"],   "HH": ["H"],  "JH": ["J"], "K": ["K"],   "L": ["L"],
    "M": ["M"],   "N": ["N"],   "NG": ["N"], "P": ["P"],   "R": ["R"],
    "S": ["S"],   "SH": ["SH"], "T": ["T"],  "TH": ["TH"], "V": ["V"],
    "W": ["V"],   "Y": ["Y"],   "Z": ["Z"],  "ZH": ["J"],
}