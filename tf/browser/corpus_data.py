"""
Access to the generated ground-truth corpus data (`bhsa_corpus_data.json`).

The JSON file is produced by `generate_corpus_data.py` from the live
corpus; regenerate it whenever the corpus version changes.  This module
provides cached loading plus lexeme search used by both the AI query
pipeline and the deterministic query validator.
"""

import json
import unicodedata
from pathlib import Path

_DATA = None
_DATA_PATH = Path(__file__).parent / "bhsa_corpus_data.json"


def load():
    """Load and cache the corpus data."""
    global _DATA
    if _DATA is None:
        with open(_DATA_PATH, encoding="utf-8") as fh:
            _DATA = json.load(fh)
        _index_lexemes(_DATA)
    return _DATA


def _strip_points(s):
    """Remove Hebrew vowel points / accents for consonantal comparison."""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", s) if not unicodedata.combining(ch)
    )


def _index_lexemes(data):
    byLex = {}
    byBase = {}
    for entry in data["lexemes"]:
        lex = entry["lex"]
        # Keep the most frequent entry per transliteration (Hebrew and
        # Aramaic homographs share a `lex` value).
        if lex not in byLex or entry["freq"] > byLex[lex]["freq"]:
            byLex[lex] = entry
        base = lex.rstrip("[/=")
        byBase.setdefault(base, [])
        if lex not in byBase[base]:
            byBase[base].append(lex)
    data["_by_lex"] = byLex
    data["_by_base"] = byBase


def all_lexemes():
    return load()["_by_lex"]


def lexeme_variants(base):
    """All actual lex values whose transliteration minus suffix marks
    equals `base` minus suffix marks (e.g. NTN -> [NTN[)."""
    return load()["_by_base"].get(base.rstrip("[/="), [])


def search_lexemes(term, max_results=8):
    """
    Search lexemes by English gloss, ETCBC transliteration, or Hebrew.

    Returns a list of dicts (lex, sp, gloss, voc, freq, lang), most
    frequent first.  Gloss matching prefers exact word matches over
    substring matches so 'give' ranks NTN[ above 'give drink'.
    """
    data = load()
    term = term.strip()
    if not term:
        return []
    exact, word, sub = [], [], []
    is_hebrew = any("֐" <= ch <= "ת" for ch in term)
    if is_hebrew:
        bare = _strip_points(term)
        for e in data["lexemes"]:
            if _strip_points(e["voc"]) == bare or e["voc"] == term:
                exact.append(e)
    else:
        tl = term.lower()
        for e in data["lexemes"]:
            gloss = e["gloss"].lower()
            if e["lex"] == term or e["lex"].rstrip("[/=") == term.rstrip("[/="):
                exact.append(e)
            elif gloss == tl:
                exact.append(e)
            elif tl in gloss.split() or tl in gloss.replace(",", " ").split():
                word.append(e)
            elif tl in gloss:
                sub.append(e)
    results = []
    seen = set()
    for bucket in (exact, word, sub):
        for e in sorted(bucket, key=lambda x: -x["freq"]):
            key = (e["lex"], e["lang"])
            if key not in seen:
                seen.add(key)
                results.append(e)
    return results[:max_results]


def feature_info(name):
    """Info dict for a feature, or None. Handles `feat@lang` forms."""
    feats = load()["features"]
    return feats.get(name)


def feature_names():
    return set(load()["features"])


def edge_features():
    return set(load()["edge_features"])


def node_types():
    return set(load()["node_types"])


def books():
    return load()["books"]
