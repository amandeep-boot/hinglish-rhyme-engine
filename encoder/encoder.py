from .maps import CONSONANT_MAP, VOWEL_MAP
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as tx

VOWELS = {"A", "AA", "I", "II", "U", "UU", "E", "O", "AY", "AW"}

def normalize(word: str) -> str:
    """
    Normalize a word by stripping whitespace and converting to lowercase.
    """
    return word.strip().lower()

def is_devanagari(word: str) -> bool:
    """
    Check if a word contains Devanagari characters.
    """
    return any('\u0900' <= ch <= '\u097F' for ch in word)

def transliterate(word: str) -> str:
    """
    Transliterate a Devanagari word into Roman script using ITRANS.
    """
    if not is_devanagari(word):
        return word
    return str(tx(word, sanscript.DEVANAGARI, sanscript.ITRANS)).lower()

def tokenize(word: str) -> list[str]:
    """
    Convert a normalized Romanized word into phonetic tokens.
    """
    tokens: list[str] = []
    i = 0

    while i < len(word):
        matched = False

        for pattern, token in CONSONANT_MAP:
            if word[i:].startswith(pattern):
                tokens.append(token)
                i += len(pattern)
                matched = True
                break

        if matched:
            continue

        for pattern, token in VOWEL_MAP:
            if word[i:].startswith(pattern):
                tokens.append(token)
                i += len(pattern)
                matched = True
                break

        if not matched:
            i += 1

    return tokens

def delete_schwa(tokens: list[str]) -> list[str]:
    """
    Drop 'A' when sandwiched between two consonants.
    """
    result: list[str] = []
    for idx, token in enumerate(tokens):
        if token == "A":
            prev_is_consonant = idx > 0 and tokens[idx - 1] not in VOWELS
            next_is_consonant = idx < len(tokens) - 1 and tokens[idx + 1] not in VOWELS
            if prev_is_consonant and next_is_consonant:
                continue
        result.append(token)
    return result

def extract_vowel_suffix(tokens: list[str]) -> list[str]:
    for token in reversed(tokens):
        if token in VOWELS:
            return [token]
    return tokens[-1:] if tokens else []

def extract_suffix(tokens: list[str], depth: int = 2) -> list[str]:
    """
    Return the last `depth` phonetic tokens as the strict rhyme suffix.
    """
    return tokens[-depth:] if len(tokens) >= depth else tokens

def encode(word: str, depth: int = 2) -> dict[str, list[str]]:
    word = normalize(word)
    word = transliterate(word)
    tokens = tokenize(word)
    tokens = delete_schwa(tokens)

    strict_suffix = extract_suffix(tokens, depth)
    vowel_suffix = extract_vowel_suffix(tokens)

    return {
        "tokens": tokens,
        "strict_suffix": strict_suffix,
        "vowel_suffix": vowel_suffix,
    }