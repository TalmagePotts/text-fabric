"""
Text-Fabric tools for the research chat agent.

Each tool is a plain function over a loaded TF advanced app.  They know
nothing about LLMs: they take simple JSON-serializable arguments and
return a dict with

- `ok`: whether the call succeeded
- `summary`: one line for the collapsed tool chip in the UI
- `detail`: the payload the model reasons over (also shown when the chip
  is expanded)

Concurrency: the browser serves requests with `run_simple(...,
threaded=True)`, so a long chat turn overlaps with ordinary searches from
the same page.  `S.search` stores per-search state on the shared `S`
object when `here=True` (the default), so every search here passes
`here=False`, exactly as the browser's own search path does
(`tf/advanced/search.py`).  A module-level lock serializes corpus access
as well, since the underlying data structures were never designed for
concurrent traversal.
"""

import collections
import threading

from .corpus_data import feature_info, search_lexemes as _search_lexemes
from .query_validator import validate_query

# Serializes all corpus access; see module docstring.
TF_LOCK = threading.Lock()

# Caps: keep tool output small enough to stay affordable as context.
SAMPLE_CAP = 20
BUCKET_CAP = 20
MAX_VERSES = 10
COUNT_CAP = 200000


def _fmt_ref(T, node):
    """'Genesis 1:1' for any node, or '' if it has no section."""
    try:
        section = T.sectionFromNode(node)
    except Exception:
        return ""
    if not section:
        return ""
    book, chapter, verse = (list(section) + [None, None])[:3]
    if chapter is None:
        return str(book)
    if verse is None:
        return f"{book} {chapter}"
    return f"{book} {chapter}:{verse}"


def _text(T, node):
    try:
        return (T.text(node) or "").strip()
    except Exception:
        return ""


def _search(app, template, limit=None):
    """
    Run a search template.  Returns (results, ok, messages).

    `here=False` keeps the shared S object untouched, and `_msgCache` as a
    list is what makes Text-Fabric hand back its diagnostics instead of
    printing them.
    """
    S = app.api.S
    msgs = []
    try:
        outcome = S.search(
            template, limit=limit, here=False, _msgCache=msgs
        )
    except Exception as e:
        return (), False, f"Execution error: {e}"
    # With _msgCache as a list and here=False, search returns
    # (results, status, messages, exe).
    if isinstance(outcome, tuple) and len(outcome) == 4:
        results, status, messages, _exe = outcome
    elif isinstance(outcome, tuple) and len(outcome) == 3:
        results, status, messages = outcome
    else:
        results, status, messages = outcome, True, ""
    try:
        results = list(results)
    except Exception as e:
        return (), False, f"Execution error: {e}"
    text = str(messages or "").strip()
    return results, bool(status), text


# ---------------------------------------------------------------------------
# tools
# ---------------------------------------------------------------------------


def search_lexemes(app, term, max_results=8):
    """Find lexemes by English gloss, ETCBC transliteration, or Hebrew."""
    term = (term or "").strip()
    if not term:
        return {"ok": False, "summary": "No search term given", "detail": {}}
    hits = _search_lexemes(term, max_results=max_results)
    if not hits:
        return {
            "ok": True,
            "summary": f"No lexeme matched “{term}”",
            "detail": {
                "term": term,
                "matches": [],
                "hint": (
                    "Nothing matched. Try a different English gloss, or "
                    "constrain by the `gloss` feature in a query instead."
                ),
            },
        }
    best = hits[0]
    return {
        "ok": True,
        "summary": (
            f"“{term}” → {best['lex']} ({best['gloss']}, {best['freq']}×)"
            + (f" and {len(hits) - 1} more" if len(hits) > 1 else "")
        ),
        "detail": {"term": term, "matches": hits},
    }


def run_query(app, template, limit=SAMPLE_CAP):
    """
    Validate and execute a search template.

    Returns the total number of results plus a small sample, each row
    with its section reference and text.
    """
    template = (template or "").strip()
    if not template:
        return {"ok": False, "summary": "Empty query", "detail": {}}

    valid, errors = validate_query(template)
    if not valid:
        return {
            "ok": False,
            "summary": "Query rejected before running",
            "detail": {
                "template": template,
                "errors": errors,
                "hint": (
                    "These are checked against the actual corpus inventory. "
                    "Fix the query and try again."
                ),
            },
        }

    T = app.api.T
    with TF_LOCK:
        results, ok, messages = _search(app, template, limit=COUNT_CAP)
        if not ok or messages:
            return {
                "ok": False,
                "summary": "Text-Fabric rejected the query",
                "detail": {"template": template, "errors": messages},
            }
        total = len(results)
        sample = []
        for row in results[: max(1, min(limit, SAMPLE_CAP))]:
            nodes = row if isinstance(row, (tuple, list)) else (row,)
            sample.append(
                {
                    "ref": _fmt_ref(T, nodes[0]),
                    "words": [_text(T, n) for n in nodes],
                }
            )

    detail = {
        "template": template,
        "total": total,
        "showing": len(sample),
        "sample": sample,
    }
    if total == 0:
        # Absence of results is not evidence of absence in the text until
        # the query itself has been checked; say so where the model reads
        # it, rather than relying on it to remember.
        detail["warning"] = (
            "0 results. This means the construction does not occur ONLY if "
            "this query expresses it correctly. Every feature value here is "
            "valid, but a valid value can still be the wrong one, and the "
            "structure (containment levels, word order, node types) may not "
            "capture what you meant. Verify before reporting absence as a "
            "finding."
        )
    elif total > len(sample):
        detail["note"] = (
            f"Showing {len(sample)} of {total}. The sample is not evidence "
            f"about proportions — use `aggregate` for that."
        )

    return {
        "ok": True,
        "summary": f"{total} result{'' if total == 1 else 's'}",
        "detail": detail,
    }


def aggregate(app, template, column, feature, top=BUCKET_CAP):
    """
    Distribution of `feature` over one column of a query's results.

    This is what turns "is X always followed by Y" into a number:
    run a query whose column N is the following word, aggregate `lex`
    over it, and read off the proportions.  `column` is 1-based.
    """
    template = (template or "").strip()
    if not template:
        return {"ok": False, "summary": "Empty query", "detail": {}}
    if feature_info(feature) is None:
        return {
            "ok": False,
            "summary": f"No such feature “{feature}”",
            "detail": {"feature": feature},
        }
    try:
        column = int(column)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "summary": "Column must be a number",
            "detail": {"column": column},
        }
    if column < 1:
        return {
            "ok": False,
            "summary": "Column is 1-based; got " + str(column),
            "detail": {"column": column},
        }

    valid, errors = validate_query(template)
    if not valid:
        return {
            "ok": False,
            "summary": "Query rejected before running",
            "detail": {"template": template, "errors": errors},
        }

    Fs = app.api.Fs
    with TF_LOCK:
        results, ok, messages = _search(app, template, limit=COUNT_CAP)
        if not ok or messages:
            return {
                "ok": False,
                "summary": "Text-Fabric rejected the query",
                "detail": {"template": template, "errors": messages},
            }
        if not results:
            return {
                "ok": True,
                "summary": "0 results — nothing to aggregate",
                "detail": {"template": template, "total": 0, "buckets": []},
            }
        width = len(results[0]) if isinstance(results[0], (tuple, list)) else 1
        if column > width:
            return {
                "ok": False,
                "summary": (
                    f"Column {column} does not exist; the query returns "
                    f"{width} column{'' if width == 1 else 's'}"
                ),
                "detail": {"template": template, "columns": width},
            }
        featureObj = Fs(feature)
        counter = collections.Counter(
            featureObj.v(row[column - 1] if isinstance(row, (tuple, list)) else row)
            for row in results
        )

    total = sum(counter.values())
    ordered = counter.most_common(max(1, min(top, BUCKET_CAP)))
    buckets = [
        {
            "value": "(none)" if value is None else str(value),
            "count": count,
            "percent": round(100.0 * count / total, 2),
        }
        for value, count in ordered
    ]
    head = buckets[0] if buckets else None
    return {
        "ok": True,
        "summary": (
            f"{total} rows; top {feature}: {head['value']} "
            f"({head['percent']}%)"
            if head
            else f"{total} rows"
        ),
        "detail": {
            "template": template,
            "column": column,
            "feature": feature,
            "total": total,
            "distinct": len(counter),
            "buckets": buckets,
        },
    }


def get_passage(app, book, chapter, verse, end_verse=None):
    """Verse text plus per-word morphology."""
    F, L, T = app.api.F, app.api.L, app.api.T
    try:
        chapter = int(chapter)
        verse = int(verse)
        endVerse = int(end_verse) if end_verse not in (None, "") else verse
    except (TypeError, ValueError):
        return {
            "ok": False,
            "summary": "Chapter and verse must be numbers",
            "detail": {"book": book, "chapter": chapter, "verse": verse},
        }
    if endVerse < verse:
        endVerse = verse
    if endVerse - verse + 1 > MAX_VERSES:
        endVerse = verse + MAX_VERSES - 1

    verses = []
    with TF_LOCK:
        for v in range(verse, endVerse + 1):
            try:
                node = T.nodeFromSection((book, chapter, v))
            except Exception:
                node = None
            if not node:
                continue
            words = []
            for w in L.d(node, otype="word"):
                words.append(
                    {
                        "text": _text(T, w),
                        "lex": F.lex.v(w),
                        "gloss": F.gloss.v(w),
                        "sp": F.sp.v(w),
                        "vs": F.vs.v(w),
                        "vt": F.vt.v(w),
                        "gn": F.gn.v(w),
                        "nu": F.nu.v(w),
                        "ps": F.ps.v(w),
                        "st": F.st.v(w),
                    }
                )
            verses.append(
                {
                    "ref": f"{book} {chapter}:{v}",
                    "text": _text(T, node),
                    "words": words,
                }
            )

    if not verses:
        return {
            "ok": False,
            "summary": f"No such passage: {book} {chapter}:{verse}",
            "detail": {
                "hint": (
                    "Book names are the Latin forms stored in the `book` "
                    "feature, e.g. Genesis, Numeri, Jesaia, Psalmi."
                )
            },
        }
    label = verses[0]["ref"] + (f"–{endVerse}" if len(verses) > 1 else "")
    return {
        "ok": True,
        "summary": f"Read {label}",
        "detail": {"verses": verses},
    }


def lexeme_profile(app, lex):
    """
    How a lexeme behaves across the corpus: frequency, glosses, stem and
    tense distribution, where it clusters, and a few references.
    """
    lex = (lex or "").strip()
    if not lex:
        return {"ok": False, "summary": "No lexeme given", "detail": {}}

    F, T = app.api.F, app.api.T
    with TF_LOCK:
        occurrences = [w for w in F.otype.s("word") if F.lex.v(w) == lex]
        if not occurrences:
            variants = _search_lexemes(lex, max_results=5)
            return {
                "ok": False,
                "summary": f"No occurrences of {lex}",
                "detail": {
                    "lex": lex,
                    "did_you_mean": variants,
                    "hint": (
                        "Lexeme values are case-sensitive and carry their "
                        "suffix marks: verbs end in `[`, nouns in `/`."
                    ),
                },
            }
        glosses = collections.Counter(
            F.gloss.v(w) for w in occurrences if F.gloss.v(w)
        )
        stems = collections.Counter(
            F.vs.v(w) for w in occurrences if F.vs.v(w) and F.vs.v(w) != "NA"
        )
        tenses = collections.Counter(
            F.vt.v(w) for w in occurrences if F.vt.v(w) and F.vt.v(w) != "NA"
        )
        parts = collections.Counter(F.sp.v(w) for w in occurrences)
        books = collections.Counter(
            (T.sectionFromNode(w) or ("?",))[0] for w in occurrences
        )
        samples = [
            {"ref": _fmt_ref(T, w), "text": _text(T, w)}
            for w in occurrences[:8]
        ]

    def top(counter, n=8):
        return [{"value": str(k), "count": v} for k, v in counter.most_common(n)]

    return {
        "ok": True,
        "summary": (
            f"{lex}: {len(occurrences)} occurrences"
            + (f", “{glosses.most_common(1)[0][0]}”" if glosses else "")
        ),
        "detail": {
            "lex": lex,
            "occurrences": len(occurrences),
            "glosses": top(glosses, 5),
            "part_of_speech": top(parts, 5),
            "stems": top(stems),
            "tenses": top(tenses),
            "top_books": top(books, 6),
            "samples": samples,
        },
    }


def list_feature_values(app, feature):
    """Valid values of a feature, with counts, from the corpus inventory."""
    feature = (feature or "").strip()
    info = feature_info(feature)
    if info is None:
        return {
            "ok": False,
            "summary": f"No such feature “{feature}”",
            "detail": {"feature": feature},
        }
    detail = {"feature": feature, "type": info["type"]}
    if info.get("description"):
        detail["description"] = info["description"]
    if info["type"] == "enum":
        values = info["values"]
        detail["values"] = [
            {"value": v, "count": c} for v, c in list(values.items())[:60]
        ]
        summary = f"{feature}: {len(values)} values"
    elif info["type"] == "int":
        detail["min"] = info.get("min")
        detail["max"] = info.get("max")
        summary = f"{feature}: integer {info.get('min')}–{info.get('max')}"
    else:
        detail["distinct_values"] = info.get("distinct_values")
        detail["sample"] = info.get("sample", [])
        summary = (
            f"{feature}: free text, {info.get('distinct_values')} distinct values"
        )
    return {"ok": True, "summary": summary, "detail": detail}


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

TOOLS = {
    "search_lexemes": search_lexemes,
    "run_query": run_query,
    "aggregate": aggregate,
    "get_passage": get_passage,
    "lexeme_profile": lexeme_profile,
    "list_feature_values": list_feature_values,
}


def call_tool(app, name, arguments):
    """
    Execute a tool by name.  Never raises: a failing tool comes back as a
    result the model can read and react to, which keeps the agent loop
    alive when it passes bad arguments.
    """
    fn = TOOLS.get(name)
    if fn is None:
        return {
            "ok": False,
            "summary": f"No such tool “{name}”",
            "detail": {"available": sorted(TOOLS)},
        }
    if not isinstance(arguments, dict):
        return {
            "ok": False,
            "summary": "Tool arguments must be an object",
            "detail": {"got": repr(arguments)[:200]},
        }
    try:
        return fn(app, **arguments)
    except TypeError as e:
        return {
            "ok": False,
            "summary": "Wrong arguments for this tool",
            "detail": {"error": str(e)},
        }
    except Exception as e:
        return {
            "ok": False,
            "summary": f"Tool failed: {type(e).__name__}",
            "detail": {"error": str(e)},
        }
