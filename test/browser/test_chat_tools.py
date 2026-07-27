"""
Tests for the chat agent's Text-Fabric tools.

Most need the BHSA corpus and are skipped where it is unavailable; the
lexeme-search tests run anywhere from the committed corpus data.

The expected numbers were taken from the live corpus, so a change here
means either the corpus version moved or a tool regressed.
"""

import pytest

from tf.browser import chat_tools
from tf.browser.corpus_data import search_lexemes


def _app():
    try:
        from tf.app import use

        return use("ETCBC/bhsa", silent="deep")
    except Exception:
        return None


APP = None


def get_app():
    global APP
    if APP is None:
        APP = _app()
    return APP


needs_corpus = pytest.mark.skipif(
    get_app() is None, reason="BHSA corpus not available on this machine"
)

# 'between' followed immediately by another word, within a clause.
BETWEEN_QUERY = "clause\n  w1:word lex=BJN/\n  w2:word\n  w1 <: w2"


class TestLexemeSearch:
    """Runs without the corpus: the lexeme list is committed."""

    def test_groups_homographs_by_lex(self):
        """BJN/ is Hebrew 'interval' (407x) and Aramaic 'between' (2x).

        Both are `lex=BJN/` in a query, so returning only the rare
        Aramaic sense would point research at the wrong word.
        """
        hits = search_lexemes("between")
        assert hits[0]["lex"] == "BJN/"
        assert hits[0]["freq"] > 400, hits[0]
        assert "between" in hits[0]["glosses"]
        assert "interval" in hits[0]["glosses"]
        assert set(hits[0]["languages"]) == {"Hebrew", "Aramaic"}

    def test_common_word_ranks_first(self):
        assert search_lexemes("give")[0]["lex"] == "NTN["
        assert search_lexemes("king")[0]["lex"] == "MLK/"

    def test_hebrew_and_transliteration(self):
        assert search_lexemes("מלך")[0]["lex"] == "MLK/"
        assert search_lexemes("NTN")[0]["lex"] == "NTN["

    def test_no_match_is_not_an_error(self):
        assert search_lexemes("zzzznotaword") == []


@needs_corpus
class TestTools:
    def test_search_lexemes_tool(self):
        r = chat_tools.search_lexemes(get_app(), "between")
        assert r["ok"]
        assert r["detail"]["matches"][0]["lex"] == "BJN/"

    def test_search_lexemes_empty(self):
        r = chat_tools.search_lexemes(get_app(), "zzzznotaword")
        assert r["ok"] and r["detail"]["matches"] == []
        assert "hint" in r["detail"]

    def test_run_query(self):
        r = chat_tools.run_query(get_app(), BETWEEN_QUERY)
        assert r["ok"], r
        assert r["detail"]["total"] == 380
        assert len(r["detail"]["sample"]) <= chat_tools.SAMPLE_CAP
        first = r["detail"]["sample"][0]
        assert ":" in first["ref"]
        assert first["words"]

    def test_run_query_rejects_bad_values_before_running(self):
        """vs=hith returns 0 results silently in TF; the validator catches it."""
        r = chat_tools.run_query(get_app(), "word vs=hith")
        assert not r["ok"]
        assert "hit" in r["detail"]["errors"]

    def test_run_query_reports_tf_errors(self):
        r = chat_tools.run_query(get_app(), "clause\n/where/\n  word sp=verb\n/-/\n/have/")
        assert not r["ok"]

    def test_aggregate_answers_always_questions(self):
        """The user's own question: is 'between' always followed by Lamed?"""
        r = chat_tools.aggregate(get_app(), BETWEEN_QUERY, 3, "lex")
        assert r["ok"], r
        assert r["detail"]["total"] == 380
        lamed = [b for b in r["detail"]["buckets"] if b["value"] == "L"]
        assert lamed and lamed[0]["count"] == 7
        assert 1.5 < lamed[0]["percent"] < 2.5
        # the answer is emphatically "no"
        assert r["detail"]["buckets"][0]["value"] == "H"

    def test_aggregate_rejects_bad_column(self):
        r = chat_tools.aggregate(get_app(), BETWEEN_QUERY, 9, "lex")
        assert not r["ok"] and "does not exist" in r["summary"]

    def test_aggregate_rejects_bad_feature(self):
        r = chat_tools.aggregate(get_app(), BETWEEN_QUERY, 2, "nosuchfeature")
        assert not r["ok"]

    def test_aggregate_handles_zero_results(self):
        r = chat_tools.aggregate(get_app(), "word lex=JHWH/ sp=adjv", 1, "lex")
        assert r["ok"] and r["detail"]["total"] == 0

    def test_lexeme_profile(self):
        r = chat_tools.lexeme_profile(get_app(), "NTN[")
        assert r["ok"], r
        assert r["detail"]["occurrences"] == 2017
        stems = {s["value"]: s["count"] for s in r["detail"]["stems"]}
        assert stems["qal"] == 1920
        assert r["detail"]["samples"][0]["ref"]

    def test_lexeme_profile_suggests_on_miss(self):
        """NTN without the verb marker does not exist; say so usefully."""
        r = chat_tools.lexeme_profile(get_app(), "NTN")
        assert not r["ok"]
        assert any(m["lex"] == "NTN[" for m in r["detail"]["did_you_mean"])

    def test_get_passage(self):
        r = chat_tools.get_passage(get_app(), "Genesis", 1, 1)
        assert r["ok"], r
        verse = r["detail"]["verses"][0]
        assert verse["ref"] == "Genesis 1:1"
        assert len(verse["words"]) == 11
        assert verse["words"][2]["lex"] == "BR>["
        assert verse["words"][2]["vs"] == "qal"

    def test_get_passage_range_is_capped(self):
        r = chat_tools.get_passage(get_app(), "Genesis", 1, 1, 99)
        assert r["ok"]
        assert len(r["detail"]["verses"]) <= chat_tools.MAX_VERSES

    def test_get_passage_uses_english_book_names(self):
        assert chat_tools.get_passage(get_app(), "Numbers", 1, 1)["ok"]

    def test_get_passage_bad_reference(self):
        r = chat_tools.get_passage(get_app(), "Nowhere", 1, 1)
        assert not r["ok"] and "hint" in r["detail"]

    def test_list_feature_values(self):
        r = chat_tools.list_feature_values(get_app(), "vs")
        assert r["ok"]
        values = {v["value"] for v in r["detail"]["values"]}
        assert "hit" in values and "hith" not in values

    def test_list_feature_values_unknown(self):
        assert not chat_tools.list_feature_values(get_app(), "nope")["ok"]

    def test_call_tool_dispatch_and_errors(self):
        assert chat_tools.call_tool(get_app(), "search_lexemes", {"term": "give"})["ok"]
        assert not chat_tools.call_tool(get_app(), "nosuchtool", {})["ok"]
        assert not chat_tools.call_tool(get_app(), "run_query", {"wrong": 1})["ok"]
        assert not chat_tools.call_tool(get_app(), "run_query", "notadict")["ok"]

    def test_call_tool_never_raises(self):
        """A tool blowing up must come back as a result, not kill the stream."""

        def boom(app, **kw):
            raise RuntimeError("kaboom")

        chat_tools.TOOLS["_boom"] = boom
        try:
            r = chat_tools.call_tool(get_app(), "_boom", {})
            assert not r["ok"] and "kaboom" in r["detail"]["error"]
        finally:
            del chat_tools.TOOLS["_boom"]
