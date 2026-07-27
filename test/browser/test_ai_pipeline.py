"""
Integration tests for the AI query pipeline against the live corpus.

Run on a machine with the BHSA corpus available (e.g. atlas):

    pytest test/browser/test_ai_pipeline.py -v

Tests in TestWithCorpus need only the corpus (no API key).
Tests in TestEndToEnd additionally need GEMINI_API_KEY or
ANTHROPIC_API_KEY in the environment; they are skipped otherwise.
Each end-to-end case asserts the pipeline returns a parseable query
whose result count falls in a sanity range.
"""

import os

import pytest

pytestmark = pytest.mark.filterwarnings("ignore")


def _corpus_app():
    try:
        from tf.app import use

        return use("ETCBC/bhsa", silent="deep")
    except Exception:
        return None


APP = None


def get_app():
    global APP
    if APP is None:
        APP = _corpus_app()
    return APP


needs_corpus = pytest.mark.skipif(
    get_app() is None, reason="BHSA corpus not available on this machine"
)

API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
needs_key = pytest.mark.skipif(
    not API_KEY, reason="no GEMINI_API_KEY / ANTHROPIC_API_KEY in environment"
)


@needs_corpus
class TestWithCorpus:
    def test_executor_counts(self):
        from tf.browser.ai_query import make_executor

        ex = make_executor(get_app())
        count, ok, messages = ex("word sp=verb vs=qal vt=wayq")
        assert ok and not messages
        assert 10000 < count < 20000  # 14,974 wayyiqtols, ~85% qal

    def test_executor_reports_parse_errors(self):
        from tf.browser.ai_query import make_executor

        ex = make_executor(get_app())
        count, ok, messages = ex("clause\n/where/\n  word sp=verb\n/-/\n/have/")
        assert not ok or messages

    def test_executor_silent_zero(self):
        from tf.browser.ai_query import make_executor

        ex = make_executor(get_app())
        count, ok, messages = ex("word vs=hith")
        assert ok and count == 0  # TF is silent — validator must catch this

    def test_diagnose_zero_finds_culprit(self):
        from tf.browser.ai_query import diagnose_zero, make_executor

        ex = make_executor(get_app())
        # JHWH/ is never an adjective: sp=adjv is the culprit constraint.
        query = "word lex=JHWH/ sp=adjv"
        report = diagnose_zero(query, ex)
        assert "sp=adjv" in report or "lex=JHWH/" in report

    def test_validator_agrees_with_engine_on_examples(self):
        """Every example in the prompt template must both validate and run."""
        import re

        from tf.browser.ai_query import build_system_prompt, make_executor
        from tf.browser.query_validator import validate_query

        ex = make_executor(get_app())
        template = build_system_prompt()
        blocks = re.findall(r"```\n(.*?)```", template, re.S)
        assert blocks, "no examples found in prompt template"
        for block in blocks:
            query = block.strip()
            ok, err = validate_query(query)
            assert ok, f"template example fails validator: {query!r}: {err}"
            count, execOk, messages = ex(query, limit=10)
            assert execOk and not messages, (
                f"template example rejected by engine: {query!r}: {messages}"
            )


EVAL_CASES = [
    # (natural language, min_results, max_results)
    ("Find all qal wayyiqtol verbs in Genesis", 1000, 3000),
    ("Find clauses where YHWH is the subject", 1500, 6000),
    ("feminine plural nouns in construct state", 800, 2500),
    ("verbless clauses inside direct speech", 4000, 15000),
    ("Find all imperatives of the verb 'give'", 100, 1000),
    ("nouns with a 2nd person masculine plural pronominal suffix", 500, 5000),
    ("clauses in Genesis without an explicit subject phrase", 3000, 9000),
    ("Hifil perfect verbs outside Genesis", 500, 5000),
    (
        "a noun directly followed by an adjective that agrees "
        "with it in gender and number",
        500,
        5000,
    ),
    ("verses containing the word for 'covenant'", 200, 600),
]


@needs_corpus
@needs_key
class TestEndToEnd:
    @pytest.mark.parametrize("prompt,lo,hi", EVAL_CASES)
    def test_eval_case(self, prompt, lo, hi):
        from tf.browser.ai_query import generate_query, make_executor

        ex = make_executor(get_app())
        result = generate_query(prompt, API_KEY, executor=ex)
        assert not result["error"], (
            f"{prompt!r} failed: {result['error']}"
        )
        assert result["query"]
        assert result["result_count"] is not None
        assert lo <= result["result_count"] <= hi, (
            f"{prompt!r} -> {result['result_count']} results, expected "
            f"[{lo}, {hi}]:\n{result['query']}"
        )
