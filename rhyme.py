"""
Query the rhyme index.

Given a word in any supported form (Devanagari, Roman Hindi, or English), encode
it to its rhyme keys and return the buckets of words that rhyme with it. Because
the index is precomputed, each lookup is a single O(1) dict access.

Two tiers of rhyme are returned:

    strict  - tight rhymes: share the strict suffix (last N phonetic tokens)
    vowel   - loose rhymes: share only the vowel anchor (the last vowel sound)

Usage:
    python rhyme.py pyaar
    python rhyme.py प्यार --limit 30
"""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

from encoder.encoder import encode

REPO_ROOT = Path(__file__).resolve().parent
INDEX_PATH = REPO_ROOT / "index" / "rhyme_index.json"


@lru_cache(maxsize=1)
def load_index() -> dict:
    """Load and cache the rhyme index from disk."""
    if not INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Index not found at {INDEX_PATH}. "
            f"Build it first: python scripts/build_index.py"
        )
    with INDEX_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _key_of(tokens: list[str]) -> str:
    return "-".join(tokens)


@lru_cache(maxsize=1)
def hindi_vocab() -> frozenset[str]:
    """
    Romanized surface forms of the Hindi corpus (e.g. "gali", "guru", "pyaar").

    Some Hindi words also exist in CMUdict as English loanwords. Auto-detecting
    purely by CMUdict membership would encode them as English at query time,
    inconsistent with how they were indexed (Hindi). The build step precomputes the
    romanized form of every Hindi word (the Hindi corpus is Devanagari) into
    `hindi_roman_vocab`; we prefer the Hindi path for any query word in this set.
    """
    index = load_index()
    return frozenset(index.get("hindi_roman_vocab", []))


def find_rhymes(word: str, limit: int = 25) -> dict:
    """
    Return rhymes for `word` as {"strict": [...], "vowel": [...]}.

    Each list holds {"word", "freq", "lang"} dicts, frequency-sorted, with the
    query word itself removed. `limit` caps the number returned per tier.
    """
    index = load_index()
    query_word = word.strip().lower()

    # Known Hindi corpus words win over an English CMUdict collision (gali, saari).
    lang_hint = "hi" if query_word in hindi_vocab() else None
    result = encode(word, lang=lang_hint)

    def lookup(index_name: str, tokens: list[str]) -> list[dict]:
        bucket = index[index_name].get(_key_of(tokens), [])
        out = []
        for entry_word, freq, lang in bucket:
            if entry_word.lower() == query_word:
                continue  # don't rhyme a word with itself
            out.append({"word": entry_word, "freq": freq, "lang": lang})
            if len(out) >= limit:
                break
        return out

    return {
        "encoding": result,
        "strict": lookup("strict_index", result["strict_suffix"]),
        "vowel": lookup("vowel_index", result["vowel_suffix"]),
    }


def _print_tier(title: str, key: str, rows: list[dict]) -> None:
    print(f"\n{title}  (key: {key})")
    if not rows:
        print("  (none)")
        return
    for row in rows:
        tag = "हिं" if row["lang"] == "hi" else "en"
        print(f"  {row['word']:<20} [{tag}]  freq={row['freq']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Find Hinglish rhymes for a word.")
    parser.add_argument("word", help="Word to rhyme (Devanagari, Roman Hindi, or English)")
    parser.add_argument("--limit", type=int, default=25, help="Max rhymes per tier")
    args = parser.parse_args()

    rhymes = find_rhymes(args.word, limit=args.limit)
    enc = rhymes["encoding"]

    print(f"Word: {args.word}  (detected: {enc['lang']})")
    print(f"Tokens: {enc['tokens']}")
    _print_tier("STRICT rhymes", _key_of(enc["strict_suffix"]), rhymes["strict"])
    _print_tier("VOWEL-anchor rhymes", _key_of(enc["vowel_suffix"]), rhymes["vowel"])


if __name__ == "__main__":
    main()
