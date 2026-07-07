"""
English phonetic encoding via CMUdict.

English spelling is not phonetic, so the Hindi orthographic encoder produces wrong
tokens for English words (e.g. "hear" and "car" both collapse to AA-R even though
they don't rhyme). Instead we look each English word up in the CMU Pronouncing
Dictionary, which gives real ARPAbet phonemes, and rewrite those phonemes into the
same unified token vocabulary the Hindi path emits (see ARPABET_MAP in maps.py).

That shared vocabulary is what makes cross-language rhymes work: "car" (K AA R) and
"pyaar" (P Y AA R) both end in AA-R and therefore rhyme.

Words absent from CMUdict (slang, proper nouns) return None so the caller can fall
back to the orthographic encoder.
"""

from __future__ import annotations

import re

import cmudict

from .maps import ARPABET_MAP

# Build the pronunciation dictionary once at import time. cmudict.dict() maps a
# lowercase word to a list of pronunciations, each a list of ARPAbet phonemes.
_CMU = cmudict.dict()

# ARPAbet marks stressed vowels with a trailing digit (AA0/AA1/AA2). Stress is
# irrelevant to our rhyme keys, so we strip it before mapping.
_STRESS = re.compile(r"\d+$")


def in_cmudict(word: str) -> bool:
    """Return True if `word` has a known English pronunciation."""
    return word.lower() in _CMU


def arpabet_to_tokens(phones: list[str]) -> list[str]:
    """
    Convert a list of ARPAbet phonemes into unified tokens.

    Stress digits are stripped; each phoneme is mapped through ARPABET_MAP, which
    may expand to more than one token (e.g. ER -> A R). Unknown phonemes are skipped.
    """
    tokens: list[str] = []
    for phone in phones:
        base = _STRESS.sub("", phone)
        tokens.extend(ARPABET_MAP.get(base, []))
    return tokens


def encode_english(word: str) -> list[str] | None:
    """
    Encode an English word to unified phonetic tokens using its CMUdict pronunciation.

    Returns None when the word is out-of-vocabulary, letting the caller fall back to
    the orthographic Hindi encoder. When a word has multiple pronunciations we take
    the first (CMUdict lists the most common variant first).
    """
    pronunciations = _CMU.get(word.lower())
    if not pronunciations:
        return None
    return arpabet_to_tokens(pronunciations[0])
