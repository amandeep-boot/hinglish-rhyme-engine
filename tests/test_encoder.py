from encoder.encoder import encode

def test_strict_rhymes():
    pairs = [
        ("pyaar", "yaar"),
        ("raat", "baat"),
        ("bhaari", "saari"),
        ("dhadkan", "dhadkan"),
    ]
    for w1, w2 in pairs:
        e1 = encode(w1)
        e2 = encode(w2)
        assert e1["strict_suffix"] == e2["strict_suffix"], (
            f"{w1} ↔ {w2} failed: {e1['strict_suffix']} vs {e2['strict_suffix']}"
        )

def test_vowel_anchor_rhymes():
    pairs = [
        ("zindagi", "gali"),
        ("zindagi", "bijli"),
    ]
    for w1, w2 in pairs:
        e1 = encode(w1)
        e2 = encode(w2)
        assert e1["vowel_suffix"] == e2["vowel_suffix"], (
            f"{w1} ↔ {w2} failed: {e1['vowel_suffix']} vs {e2['vowel_suffix']}"
        )

def test_non_rhymes_dont_match():
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
        assert e1["vowel_suffix"] != e2["vowel_suffix"], (
            f"{w1} and {w2} should not vowel-rhyme: "
            f"{e1['vowel_suffix']} vs {e2['vowel_suffix']}"
        )