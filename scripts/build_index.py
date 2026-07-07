"""
Build the rhyme index from frequency word lists.

Reads one or more `word<space>frequency` corpora, runs every word through the
phonetic encoder, and buckets words by their rhyme keys into an inverted index:

    rhyme_key  ->  [ [word, freq, lang], ... ]   (sorted by freq, descending)

Two indexes are produced, one per rhyme strictness level:

    strict_index  keyed by the strict suffix  (last N phonetic tokens; tight rhymes)
    vowel_index   keyed by the vowel anchor    (last vowel token; looser rhymes)

The whole point of precomputing this offline is that a query at runtime is a
single O(1) dict lookup: encode the input word -> look up its key -> get the
bucket of everything that rhymes with it.

Usage:
    python scripts/build_index.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# Allow `from encoder.encoder import encode` when run from the repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from encoder.encoder import (  # noqa: E402
    encode,
    is_devanagari,
    normalize,
    normalize_roman,
    transliterate,
)

DATA_DIR = REPO_ROOT / "data"
INDEX_DIR = REPO_ROOT / "index"
INDEX_PATH = INDEX_DIR / "rhyme_index.json"

# Corpora to ingest: (filename, language tag, max words to keep).
# Files are frequency-ranked, so "keep top N" == "keep the N most common words".
CORPORA = [
    ("hi_full.txt", "hi", 21309),
    ("en_50k.txt", "en", 50000),
]

# A rhyme key must have at least this many tokens to be worth indexing. A
# single-token suffix (e.g. one bare vowel) rhymes with far too much to be useful
# in the strict index, but is exactly what we want for the vowel anchor.
MIN_STRICT_TOKENS = 2


def key_of(tokens: list[str]) -> str:
    """Join a list of phonetic tokens into a single hashable string key."""
    return "-".join(tokens)


def is_indexable(word: str) -> bool:
    """
    Skip corpus entries that are not real words: pure punctuation, digits, or
    stray symbols. We keep anything containing a Devanagari or Latin letter.
    """
    if not word:
        return False
    return any(ch.isalpha() or is_devanagari(ch) for ch in word)


def load_corpus(path: Path, lang: str, limit: int) -> list[tuple[str, int]]:
    """
    Parse a `word<space>frequency` file into (word, freq) pairs, keeping the top
    `limit` indexable entries. Malformed lines are skipped defensively.
    """
    entries: list[tuple[str, int]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) != 2:
                continue
            word, raw_freq = parts
            if not is_indexable(word):
                continue
            try:
                freq = int(raw_freq)
            except ValueError:
                continue
            entries.append((word, freq))
            if len(entries) >= limit:
                break
    return entries


def build() -> dict:
    """Ingest every corpus and return the assembled index structure."""
    strict_index: dict[str, list[list]] = defaultdict(list)
    vowel_index: dict[str, list[list]] = defaultdict(list)

    total_words = 0
    skipped = 0
    oov_en = 0  # English corpus words absent from CMUdict (fell back to Hindi encoder)

    # Romanized surface forms of the Hindi corpus (e.g. गली -> "gali"). At query
    # time this lets rhyme.py recognize a romanized Hindi word that also collides
    # with an English CMUdict entry (gali, guru, saari) and keep it on the Hindi
    # path, consistent with how it was indexed.
    hindi_roman: set[str] = set()

    for filename, lang, limit in CORPORA:
        path = DATA_DIR / filename
        if not path.exists():
            print(f"  ! missing corpus: {path} (skipping)")
            continue

        corpus = load_corpus(path, lang, limit)
        print(f"  {filename}: {len(corpus)} words")

        for word, freq in corpus:
            # Pass the corpus's known language so English words take the CMUdict
            # path and Hindi words the orthographic path — no per-word guessing.
            result = encode(word, lang=lang)
            strict = result["strict_suffix"]
            vowel = result["vowel_suffix"]

            # An 'en' word that came back tagged 'hi' was out-of-vocabulary in
            # CMUdict and fell back to the orthographic encoder.
            if lang == "en" and result["lang"] != "en":
                oov_en += 1

            # Record the romanized form of Hindi words for query-time disambiguation.
            if lang == "hi":
                roman = normalize_roman(normalize(transliterate(word)))
                if roman:
                    hindi_roman.add(roman)

            if not strict:
                skipped += 1
                continue

            entry = [word, freq, lang]

            if len(strict) >= MIN_STRICT_TOKENS:
                strict_index[key_of(strict)].append(entry)
            if vowel:
                vowel_index[key_of(vowel)].append(entry)

            total_words += 1

    # Sort each bucket by frequency (descending) so the most usable, common
    # rhymes surface first at query time.
    def sort_buckets(index: dict[str, list[list]]) -> dict[str, list[list]]:
        return {
            key: sorted(bucket, key=lambda e: e[1], reverse=True)
            for key, bucket in index.items()
        }

    return {
        "meta": {
            "total_words": total_words,
            "skipped": skipped,
            "oov_en": oov_en,
            "strict_keys": len(strict_index),
            "vowel_keys": len(vowel_index),
            "min_strict_tokens": MIN_STRICT_TOKENS,
            "corpora": [c[0] for c in CORPORA],
            "hindi_roman_vocab_size": len(hindi_roman),
        },
        "strict_index": sort_buckets(strict_index),
        "vowel_index": sort_buckets(vowel_index),
        "hindi_roman_vocab": sorted(hindi_roman),
    }


def main() -> None:
    print("Building rhyme index...")
    index = build()

    INDEX_DIR.mkdir(exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False)

    meta = index["meta"]
    print(
        f"Done. indexed={meta['total_words']} skipped={meta['skipped']} "
        f"oov_en={meta['oov_en']} "
        f"strict_keys={meta['strict_keys']} vowel_keys={meta['vowel_keys']}"
    )
    print(f"Wrote {INDEX_PATH}")


if __name__ == "__main__":
    main()
