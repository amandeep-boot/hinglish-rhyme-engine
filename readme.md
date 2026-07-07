# Hinglish Rhyme Engine

A rule-based phonetic rhyme engine for Hindi, Hinglish, and English. Given a word
in any of those forms, it returns the words that rhyme with it — including
**cross-language rhymes** (e.g. `pyaar` ↔ `car`), which is the point of a *Hinglish*
engine.

## Current status

Working end-to-end pipeline: **encoder → offline index → query**.

- Language-aware phonetic encoder (Hindi orthographic rules **or** real English
  pronunciation via CMUdict).
- Precomputed inverted rhyme index over ~71k words (Hindi + English corpora).
- CLI query tool with two rhyme tiers (strict + vowel-anchor).
- 15 passing tests.

Not yet built: a FastAPI query layer, and cross-language frequency balancing
(see [Roadmap](#roadmap--pick-up-and-continue)).

## Project structure

```text
hinglish-rhyme-engine/
├── encoder/
│   ├── __init__.py
│   ├── encoder.py        # encode() dispatcher + Hindi orthographic path
│   ├── english.py        # CMUdict-backed English path
│   └── maps.py           # Hindi consonant/vowel maps + ARPABET_MAP
├── scripts/
│   └── build_index.py    # builds the offline rhyme index from corpora
├── data/                 # frequency word lists (hi_full.txt, en_50k.txt)
├── index/
│   └── rhyme_index.json  # generated inverted index (rebuildable)
├── rhyme.py              # CLI: query the index
├── tests/
│   └── test_encoder.py
└── requirements.txt
```

## Architecture

Three stages. The encoder is the core; everything else is built around it.

```text
                 ┌────────────────────────────────────────────────┐
   word ────────▶│  encode()  — language-aware phonetic encoder    │
                 └────────────────────────────────────────────────┘
                                     │ phonetic tokens + rhyme suffixes
              build time             │              query time
        ┌───────────────────┐        │        ┌───────────────────────┐
        │ build_index.py     │◀───────┴───────▶│ rhyme.py              │
        │ every corpus word  │                 │ encode the query word │
        │ → bucket by suffix │                 │ → O(1) dict lookup    │
        └───────────────────┘                 └───────────────────────┘
                 │                                        │
                 ▼                                        ▼
        index/rhyme_index.json  ───────────────▶  rhyming words
```

The index is precomputed offline so that a query at runtime is a single O(1) dict
access: encode the input word → look up its rhyme key → return the bucket of
everything sharing that key.

### The encoder is a language dispatcher

`encode(word, depth=2, lang=None)` (in `encoder/encoder.py`) routes each word to the
backend that actually reflects how it is pronounced:

```text
encode(word)
  ├─ is Devanagari?              → Hindi orthographic path
  ├─ in CMUdict (or lang="en")?  → English path (real phonemes); OOV → Hindi path
  └─ else (romanized Hindi/OOV)  → Hindi orthographic path
```

Both paths emit tokens in **one shared vocabulary**, then feed the same
suffix-extraction step. Keeping the vocabulary shared is what lets a Hindi word and
an English word land in the same rhyme bucket. It returns:

```python
encode("car") -> {
  "tokens":        ["K", "AA", "R"],
  "strict_suffix": ["AA", "R"],   # tight rhyme key (last N tokens)
  "vowel_suffix":  ["AA"],        # loose rhyme key (last vowel sound)
  "lang":          "en",          # path actually taken
}
```

## Phonetic algorithm & design choices

### 1. Normalization
Strip/lowercase. Devanagari is detected by Unicode block (`ऀ`–`ॿ`).

### 2. Hindi path (orthographic)
Hindi/romanized-Hindi spelling is (near) phonetic, so we can encode from letters:

1. **Transliterate** Devanagari → Roman (ITRANS, via `indic-transliteration`).
2. **`normalize_roman`** — collapse exaggerated vowels (`yaaaar`→`yaar`), fix
   transliteration artifacts, normalize word-final vowels, `-ar`→`-aar`, a few
   exceptions.
3. **`tokenize`** — greedy longest-match over `CONSONANT_MAP` / `VOWEL_MAP`
   (`maps.py`). Aspirated clusters (`bh`, `dh`, `kh`…) and retroflexes are matched
   before single consonants; `v`/`w` merge, `q`→`K`, etc.
4. **`delete_schwa`** — drop the inherent `A` when sandwiched between two consonants
   (`sapna` → `S-P-N-A`, not `S-A-P-N-A`). This models Hindi schwa deletion and is
   **Hindi-only** — English phonemes are already real sounds and must not be touched.

### 3. English path (CMUdict)
English spelling is **not** phonetic (`hear` and `car` share the letters `-ar` but
don't rhyme). So instead of guessing from letters we look the word up in the **CMU
Pronouncing Dictionary**, which returns ARPAbet phonemes, and rewrite them into the
shared token vocabulary (`encoder/english.py`, `ARPABET_MAP` in `maps.py`):

- Stress digits are stripped (`AA1` → `AA`).
- Consonants map ~1:1 (`K`, `R`, `T`…); a few merge (`W`→`V`, `NG`→`N`, `ZH`→`J`).
- **Vowels are deliberately lossy** — ARPAbet has more vowel distinctions than the
  Hindi token set, so several collapse onto the nearest Hindi vowel:

  | ARPAbet | → | ARPAbet | → | ARPAbet | → |
  |---|---|---|---|---|---|
  | AA | AA | EH | E | OW | O |
  | AE | A | ER | A R | OY | O Y |
  | AH | A | EY | E | UH | U |
  | AO | O | IH | I | UW | UU |
  | AW | AW | IY | II | AY | AY |

  `ER`/`OY` expand to two tokens so the trailing consonantal sound still counts
  toward the rhyme (`her` → `H A R`, `boy` → `B O Y`).

Words absent from CMUdict (~20% of the English corpus: inflections, proper nouns,
slang) **fall back** to the Hindi orthographic encoder rather than being dropped.

### 4. Rhyme suffix extraction
Two tiers, both derived from the token list:

- **strict** (`extract_suffix`, depth 2) — the last N tokens. Tight rhymes:
  `raat`/`baat` → `AA-T`.
- **vowel-anchor** (`extract_vowel_suffix`) — the last vowel token only. Loose
  rhymes / assonance: `zindagi`/`gali` → `I`.

### 5. Cross-language rhyming
Because both paths emit the same symbols, `pyaar` (Hindi → `P Y AA R`) and `car`
(English → `K AA R`) both reduce to strict suffix `AA-R` and rhyme.

### 6. Language detection & the romanized-collision choice
At query time the language is auto-detected (CMUdict membership ⇒ English). The
tricky case: some romanized Hindi words (`gali`, `guru`, `saari`) **also exist in
CMUdict** as English loanwords, so naive detection would encode them as English and
miss their Hindi rhyme bucket.

**Policy (chosen): Hindi wins for known corpus words.** The Hindi corpus is
Devanagari, so `build_index.py` precomputes the *romanized* form of every Hindi word
into `hindi_roman_vocab`. `rhyme.py` checks that set and pins `lang="hi"` for
matching queries. The encoder itself stays pure (no index dependency) — the
disambiguation lives in the query layer.

## The rhyme index

`build_index.py` ingests each corpus with its **known** language (so English corpus
words take the CMUdict path and Hindi words the orthographic path — no per-word
guessing at build time), encodes every word, and buckets them into two inverted
indexes:

```text
strict_index[suffix] -> [[word, freq, lang], ...]   # sorted by freq desc
vowel_index[suffix]  -> [[word, freq, lang], ...]
```

`meta` records `total_words`, `skipped`, `oov_en` (English words that fell back),
key counts, and `hindi_roman_vocab_size`. Strict keys need ≥ `MIN_STRICT_TOKENS` (2)
tokens to be worth indexing; a single bare vowel rhymes with too much to be useful
as a strict key but is exactly the vowel-anchor key.

Latest build: `indexed=70708 skipped=601 oov_en=10206 strict_keys=871 vowel_keys=37`.

## Run locally

```bash
pip install -r requirements.txt        # indic-transliteration, cmudict, pytest, ...

python scripts/build_index.py          # build index/rhyme_index.json (needed once)

python rhyme.py pyaar                   # query
python rhyme.py प्यार --limit 30        # Devanagari also works
python rhyme.py hear                    # English

python -m pytest tests -v              # run tests
```

> On Windows, prefix with `PYTHONIOENCODING=utf-8` when printing Devanagari.

## API shape

```python
from encoder.encoder import encode
encode(word, depth=2, lang=None) -> {
  "tokens": [...], "strict_suffix": [...], "vowel_suffix": [...], "lang": "hi"|"en"
}

from rhyme import find_rhymes
find_rhymes(word, limit=25) -> {
  "encoding": {...},
  "strict":  [{"word", "freq", "lang"}, ...],
  "vowel":   [{"word", "freq", "lang"}, ...],
}
```

## Roadmap / pick up and continue

### Done
- [x] Language-aware encoder (Hindi orthographic + English CMUdict), unified token space.
- [x] Cross-language rhyming (`pyaar` ↔ `car`).
- [x] Romanized-collision disambiguation (`gali`, `guru` → Hindi).
- [x] Offline inverted index over Hindi + English corpora.
- [x] CLI query tool with strict + vowel-anchor tiers.
- [x] 15 tests (Hindi phonetics, English correctness, cross-language, routing, OOV).

### Next up (in priority order)
1. **Frequency balancing across languages (Problem B).** English corpus frequencies
   (100k–4M) dwarf Hindi ones, so a Hindi query currently returns mostly English
   results even though Hindi words are in the bucket. Options: normalize freq
   per-corpus (percentile / `freq ÷ corpus_max`), round-robin by language at query
   time, and/or a `--lang` filter on `rhyme.py` (entries are already tagged).
2. **Clean up Hindi transliteration artifacts.** Some indexed Hindi words carry a
   stray trailing `r`/halant residue (e.g. `मार्`, `अंगरr`). Tighten `normalize_roman`
   / the ITRANS handling.
3. **FastAPI query layer.** Wrap `find_rhymes` in an HTTP endpoint (deps already in
   `requirements.txt`).
4. **Improve the English↔Hindi vowel mapping** where the lossy collapse hurts recall
   (e.g. the `IH`/`IY`-before-`R` split means `hear`≠`clear` in the strict tier).

### Where things live (for a fast restart)
- Encoding logic & language dispatch: `encoder/encoder.py`
- English pronunciation + ARPAbet mapping: `encoder/english.py`, `ARPABET_MAP` in `encoder/maps.py`
- Index build (corpora, lang hints, romanized vocab): `scripts/build_index.py`
- Query + disambiguation: `rhyme.py`
- Corpora config: `CORPORA` in `scripts/build_index.py`

## Goal

Start simple, validate the encoder, and improve the product gradually.
