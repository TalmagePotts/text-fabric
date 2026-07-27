"""
Generate ground-truth corpus data for the AI query generator.

Run this on a machine with the BHSA corpus loaded (e.g. atlas):

    python -m tf.browser.generate_corpus_data [output_path]

It produces `bhsa_corpus_data.json` next to this file (or at output_path),
containing:

- node types (in embedding order)
- every node feature with its full value inventory (or a marker for
  open/integer features)
- edge feature names
- book names (Latin, as stored in the `book` feature) and their English
  equivalents
- the full lexeme list with transliteration, part of speech, gloss,
  vocalized Hebrew, frequency, and language

The AI query pipeline uses this file to validate generated queries and to
build its prompt, so the reference material can never drift from the
corpus actually being served.  Re-run after upgrading the corpus.
"""

import json
import sys
from collections import Counter
from pathlib import Path

# Features whose value inventories are too large to enumerate usefully.
# They are validated by other means (lex against the lexeme list) or not
# at all (free-text features).
MAX_ENUM_VALUES = 250


def generate(output_path=None):
    from tf.app import use

    A = use("ETCBC/bhsa", silent="deep")
    api = A.api
    F, Fs, T, C = api.F, api.Fs, api.T, api.C

    tf = api.TF

    data = {
        "corpus": "ETCBC/bhsa",
        "node_types": [level[0] for level in C.levels.data],
        "features": {},
        "edge_features": [],
        "books": [],
        "lexemes": [],
    }

    # --- node features with value inventories ---------------------------
    # Iterate the full feature registry (not just what happens to be
    # loaded) so features like `kind` are included.
    for feat in sorted(tf.features):
        if feat in ("otype", "oslots") or feat.startswith("__"):
            continue
        fObj = tf.features[feat]
        if getattr(fObj, "isConfig", False):
            continue
        if getattr(fObj, "isEdge", False):
            data["edge_features"].append(feat)
            continue
        try:
            fObj.load(silent="deep")
            freq = Counter(v for v in fObj.data.values() if v is not None)
        except Exception as e:
            print(f"skipping {feat}: {e}")
            continue
        ordered = freq.most_common()
        isInt = ordered and all(isinstance(v, int) for v, _ in ordered)
        entry = {"description": (fObj.metaData or {}).get("description", "")}
        if isInt:
            entry["type"] = "int"
            entry["min"] = min(freq)
            entry["max"] = max(freq)
        elif len(ordered) > MAX_ENUM_VALUES:
            entry["type"] = "open"
            entry["distinct_values"] = len(ordered)
            entry["sample"] = [str(v) for v, _ in ordered[:10]]
        else:
            entry["type"] = "enum"
            entry["values"] = {str(v): n for v, n in ordered}
        data["features"][feat] = entry

    # --- books ----------------------------------------------------------
    for b in F.otype.s("book"):
        data["books"].append(
            {
                "latin": F.book.v(b),
                "english": T.sectionFromNode(b, lang="en")[0],
            }
        )

    # --- lexemes --------------------------------------------------------
    for lx in F.otype.s("lex"):
        data["lexemes"].append(
            {
                "lex": F.lex.v(lx),
                "sp": F.sp.v(lx),
                "gloss": F.gloss.v(lx) or "",
                "voc": F.voc_lex_utf8.v(lx) or "",
                "freq": F.freq_lex.v(lx) or 0,
                "lang": F.language.v(lx) or "",
            }
        )

    out = (
        Path(output_path)
        if output_path
        else Path(__file__).parent / "bhsa_corpus_data.json"
    )
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)
    print(f"Wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    print(
        f"{len(data['features'])} features, {len(data['lexemes'])} lexemes, "
        f"{len(data['books'])} books"
    )


if __name__ == "__main__":
    generate(sys.argv[1] if len(sys.argv) > 1 else None)
