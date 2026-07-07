from .maps import CONSONANT_MAP, VOWEL_MAP
from .english import encode_english, in_cmudict
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as tx
import re

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

def normalize_roman(word: str) -> str:
    word = word.lower().strip()

    # 1. collapse exaggerated vowels
    word = re.sub(r'a{3,}', 'aa', word)
    word = re.sub(r'e{3,}', 'ee', word)
    word = re.sub(r'i{3,}', 'i', word)
    word = re.sub(r'o{3,}', 'oo', word)
    word = re.sub(r'u{3,}', 'uu', word)

    # 2. transliteration artifact: consonant + yara -> consonant + yaar
    word = re.sub(r'([bcdfghjklmnpqrstvwxyz])yara$', r'\1yaar', word)

    # 3. word-final vowel normalization
    if word.endswith("ee"):
        word = word[:-2] + "i"
    if word.endswith("oo"):
        word = word[:-2] + "u"

    # 4. word-final -ar -> -aar
    if word.endswith("ar") and not word.endswith("aar"):
        word = word[:-2] + "aar"

    # 5. piy- -> py-
    word = re.sub(r'^piy', 'py', word)

    # 6. rare transliteration exceptions
    exceptions = {
        "zimdagi": "zindagi",
    }
    return exceptions.get(word, word)

def _encode_hindi(word: str) -> list[str]:
    """
    Encode a Devanagari or romanized-Hindi word into phonetic tokens using the
    orthographic rules: transliterate, normalize spelling, tokenize, delete schwa.
    """
    word = transliterate(word)
    word = normalize_roman(word)
    tokens = tokenize(word)
    return delete_schwa(tokens)


def encode(word: str, depth: int = 2, lang: str | None = None) -> dict:
    """
    Encode a word into phonetic tokens and rhyme suffixes, routing by language.

    Three paths all emit the same unified token vocabulary:
      - Devanagari              -> Hindi orthographic encoder
      - English (in CMUdict)    -> CMUdict phonemes (real pronunciation)
      - romanized Hindi / OOV   -> Hindi orthographic encoder

    `lang` is an optional hint ('hi'/'en'). When omitted, English is auto-detected
    via CMUdict membership. English words absent from CMUdict fall back to the Hindi
    encoder. The returned dict includes the path actually taken as "lang".
    """
    word = normalize(word)

    use_english = (
        not is_devanagari(word)
        and (lang == "en" or (lang is None and in_cmudict(word)))
    )

    detected = "hi"
    tokens: list[str] | None = None
    if use_english:
        tokens = encode_english(word)  # None if OOV
        if tokens is not None:
            detected = "en"
    if tokens is None:
        tokens = _encode_hindi(word)

    strict_suffix = extract_suffix(tokens, depth)
    vowel_suffix = extract_vowel_suffix(tokens)

    return {
        "tokens": tokens,
        "strict_suffix": strict_suffix,
        "vowel_suffix": vowel_suffix,
        "lang": detected,
    }

