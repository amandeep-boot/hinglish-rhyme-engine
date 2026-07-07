from encoder.encoder import encode
from encoder.encoder import normalize_roman

# These pairs test the Hindi phonetic path. A couple of the words (saari, gali)
# also exist in CMUdict as English loanwords, so we pin lang="hi" to test Hindi
# phonetics directly. At query time, rhyme.py resolves this collision by preferring
# the Hindi path for known Hindi corpus words.
def test_strict_rhymes():
    pairs = [
        ("pyaar", "yaar"),
        ("raat", "baat"),
        ("bhaari", "saari"),
        ("dhadkan", "dhadkan"),
    ]
    for w1, w2 in pairs:
        e1 = encode(w1, lang="hi")
        e2 = encode(w2, lang="hi")
        assert e1["strict_suffix"] == e2["strict_suffix"], (
            f"{w1} ↔ {w2} failed: {e1['strict_suffix']} vs {e2['strict_suffix']}"
        )


def test_vowel_anchor_rhymes():
    pairs = [
        ("zindagi", "gali"),
        ("zindagi", "bijli"),
    ]
    for w1, w2 in pairs:
        e1 = encode(w1, lang="hi")
        e2 = encode(w2, lang="hi")
        assert e1["vowel_suffix"] == e2["vowel_suffix"], (
            f"{w1} ↔ {w2} failed: {e1['vowel_suffix']} vs {e2['vowel_suffix']}"
        )


def test_strict_non_rhymes_dont_match():
    pairs = [
        ("pyaar", "zindagi"),
        ("raat", "subah"),
    ]
    for w1, w2 in pairs:
        e1 = encode(w1)
        e2 = encode(w2)

        assert e1["strict_suffix"] != e2["strict_suffix"], (
            f"{w1} and {w2} should not strict-rhyme: "
            f"{e1['strict_suffix']} vs {e2['strict_suffix']}"
        )

def test_alternate_spellings_collapse():
    pairs = [
        ("pyaar", "pyar"),
        ("pyaar", "piyar"),
        ("khushi", "khushee"),
        ("zindagi", "zindagee"),
    ]
    for w1, w2 in pairs:
        e1 = encode(w1)
        e2 = encode(w2)
        assert e1["tokens"] == e2["tokens"], (
            f"{w1} and {w2} should encode the same: "
            f"{e1['tokens']} vs {e2['tokens']}"
        )

def test_devanagari_and_roman_match():
    pairs = [
        ("प्यार", "pyaar"),
        ("सपना", "sapna"),
        ("खुशी", "khushi"),
        ("ज़िंदगी", "zindagi"),
    ]
    for w1, w2 in pairs:
        e1 = encode(w1)
        e2 = encode(w2)
        assert e1["tokens"] == e2["tokens"], (
            f"{w1} and {w2} should transliterate to same tokens: "
            f"{e1['tokens']} vs {e2['tokens']}"
        )


def test_schwa_deletion_consistency():
    words = [
        "sapna",
        "karma",
        "rasta",
    ]
    for word in words:
        e1 = encode(word)
        e2 = encode(word)
        assert e1["tokens"] == e2["tokens"], (
            f"{word} should encode consistently: "
            f"{e1['tokens']} vs {e2['tokens']}"
        )


def test_urdu_spelling_variants():
    pairs = [
        ("ishq", "ishk"),
    ]
    for w1, w2 in pairs:
        e1 = encode(w1)
        e2 = encode(w2)
        assert e1["vowel_suffix"] == e2["vowel_suffix"], (
            f"{w1} ↔ {w2} should share vowel anchor: "
            f"{e1['vowel_suffix']} vs {e2['vowel_suffix']}"
        )


def test_long_vowel_endings_match():
    pairs = [
        ("khwaab", "kitaab"),
    ]
    for w1, w2 in pairs:
        e1 = encode(w1)
        e2 = encode(w2)
        assert e1["strict_suffix"] == e2["strict_suffix"], (
            f"{w1} ↔ {w2} should share strict suffix: "
            f"{e1['strict_suffix']} vs {e2['strict_suffix']}"
        )


def test_same_word_same_encoding():
    words = [
        "pyaar",
        "zindagi",
        "bhaari",
        "sapna",
        "ishq",
    ]
    for word in words:
        e1 = encode(word)
        e2 = encode(word)
        assert e1 == e2, f"{word} should encode identically on repeated runs"


def test_normalize_roman_variants():
    assert normalize_roman("pyar") == normalize_roman("pyaar")
    assert normalize_roman("khushee") == normalize_roman("khushi")
    assert normalize_roman("zindagee") == normalize_roman("zindagi")


# --- Language-aware encoding (English via CMUdict) ---

def test_english_rhymes_are_correct():
    # Words that genuinely rhyme should share a strict suffix.
    groups = [
        ["car", "far", "star"],      # AA-R
        ["clear", "year", "dear"],   # I-R
        ["hear", "here"],            # II-R
    ]
    for group in groups:
        suffixes = [encode(w)["strict_suffix"] for w in group]
        assert all(s == suffixes[0] for s in suffixes), (
            f"{group} should share a strict suffix, got {suffixes}"
        )


def test_english_non_rhymes_separate():
    # The old orthographic encoder wrongly bucketed all -ar spellings together.
    # These groups sound different and must NOT share a strict suffix.
    assert encode("car")["strict_suffix"] != encode("hear")["strict_suffix"]
    assert encode("car")["strict_suffix"] != encode("clear")["strict_suffix"]
    assert encode("war")["strict_suffix"] != encode("car")["strict_suffix"]


def test_cross_language_rhymes():
    # The headline Hinglish feature: Hindi and English words rhyme in one space.
    aa_r = encode("car")["strict_suffix"]
    for w in ["pyaar", "yaar", "star", "far"]:
        assert encode(w)["strict_suffix"] == aa_r, (
            f"{w} should cross-language rhyme with 'car' ({aa_r}), "
            f"got {encode(w)['strict_suffix']}"
        )


def test_language_routing():
    assert encode("car")["lang"] == "en"       # in CMUdict -> English path
    assert encode("pyaar")["lang"] == "hi"      # OOV -> Hindi path
    assert encode("zindagi")["lang"] == "hi"
    # Explicit hint forces the Hindi orthographic path even for an English word.
    assert encode("car", lang="hi")["lang"] == "hi"


def test_oov_english_falls_back():
    # A plausible English-looking OOV word must still encode without error.
    result = encode("zzxqplt")
    assert result["lang"] == "hi"
    assert isinstance(result["tokens"], list)