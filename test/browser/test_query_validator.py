"""Unit tests for the deterministic query validator.

These run anywhere (no corpus needed — they use the committed
bhsa_corpus_data.json).  Run with:  pytest test/browser/test_query_validator.py
"""

import pytest

from tf.browser.query_validator import validate_query
from tf.browser.corpus_data import search_lexemes


GOOD_QUERIES = [
    "word sp=verb",
    "word lex=JHWH/",
    "word sp=subs gn=f nu=pl",
    "word sp=verb vs=qal vt=perf",
    "book book=Genesis\n  word sp=verb",
    "book book@en=Numbers\n  word sp=verb",
    "clause kind=VC\n  word sp=verb vt=wayq",
    "clause\n  vb:word sp=verb\n  n:word sp=subs\n  vb < n",
    "sentence\n  v:word sp=verb\n  n:word sp=subs\n  v :> n",
    "clause\n/without/\n  word sp=verb\n/-/",
    "word gn=f\n/without/\n.. nu=pl\n/-/",
    "word freq_lex>1000",
    "word lex~^NTN",
    "word sp=verb|subs",
    "word sp#prep",
    "c:clause_atom\nm:clause_atom\nc -mother> m",
    "% a comment\nword sp=verb",
    "clause typ=WayX\n  phrase function=Pred\n    word vs=hif",
    "word lex=NTN[ vt=impv",
    "verse\n  w1:word sp=verb\n  w2:word sp=verb\n  w1 <3: w2",
    "word\n  sp=verb\n  vt=wayq",  # feature continuation lines
]

BAD_QUERIES = [
    # (query, expected substring of error)
    ("word pos=verb", "sp"),
    ("word gender=m", "gn"),
    ("word sp=verbb", "did you mean"),
    ("word vs=hith", "hit"),
    ("word lex=NTN", "NTN["),
    ("word lex=YHWH", "does not exist"),
    ("word vt=participle", "not a value"),
    ("phrase function=Predicate", "not a value"),
    ("word sp~[", "invalid regex"),
    ("word freq_lex~100", "integer feature"),
    ("word sp>verb", "not an integer feature"),
    ("wrod sp=verb", "did you mean"),
    ("clause\n  w1:word sp=verb\n  w1 < w2", "not a defined name"),
    ("c:clause -motherr> m:clause\n", "unknown edge feature"),
    ("book book=Numbers", "did you mean"),  # English name; feature is Latin
    ("", "empty"),
]


@pytest.mark.parametrize("query", GOOD_QUERIES)
def test_good_queries_pass(query):
    ok, err = validate_query(query)
    assert ok, f"expected valid, got: {err}"


@pytest.mark.parametrize("query,expected", BAD_QUERIES)
def test_bad_queries_fail(query, expected):
    ok, err = validate_query(query)
    assert not ok, f"expected invalid: {query!r}"
    assert expected in err, f"expected {expected!r} in error, got: {err}"


def test_lexeme_search_english():
    results = search_lexemes("give")
    assert results
    assert results[0]["lex"] == "NTN[", results
    assert results[0]["freq"] > 1000


def test_lexeme_search_translit():
    results = search_lexemes("NTN")
    assert results and results[0]["lex"] == "NTN["


def test_lexeme_search_hebrew():
    results = search_lexemes("מלך")
    assert results
    assert any(e["lex"].startswith("MLK") for e in results)


def test_lexeme_search_king():
    results = search_lexemes("king")
    assert any(e["lex"] == "MLK/" for e in results)
