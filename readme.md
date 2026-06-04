# Hinglish Rhyme Engine

A rule-based phonetic rhyme engine for Hindi, Hinglish, and English.

## Current status

The project currently includes a first-pass encoder that:
- normalizes input words,
- transliterates Devanagari to Roman form,
- converts words into phonetic tokens,
- applies simple schwa deletion,
- extracts strict and vowel-anchor rhyme suffixes.

## Project structure

```text
hinglish-rhyme-engine/
├── encoder/
│   ├── __init__.py
│   ├── encoder.py
│   └── maps.py
├── tests/
│   └── test_encoder.py
└── requirements.txt
```

## Run locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest tests -v
```

## Current API shape

```python
encode(word) -> {
  "tokens": [...],
  "strict_suffix": [...],
  "vowel_suffix": [...]
}
```

## Near-term plan

1. Expand encoder test coverage.
2. Improve phonetic rules and schwa handling.
3. Build a word corpus and rhyme index.
4. Add a FastAPI query layer.

## Goal

Start simple, validate the encoder, and improve the product gradually.