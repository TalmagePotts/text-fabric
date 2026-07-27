"""
Agent loop tests with a stubbed provider (no corpus, no API key).

These check the control flow that is easy to get wrong: the tool budget,
tool failures being reported back to the model instead of crashing the
stream, and every requested tool call receiving a result (Claude rejects
an assistant turn whose tool_use blocks are left unanswered).
"""

import pytest

from tf.browser import chat_agent


class FakeAdapter:
    """Replays a scripted sequence of model turns."""

    def __init__(self, script):
        self.script = list(script)
        self.seen = []  # messages as of each turn
        self.results = []  # tool_results messages it was handed

    def turn(self, messages):
        self.seen.append(list(messages))
        if not self.script:
            return "fallback answer", [], {"role": "assistant", "content": "done"}
        text, calls = self.script.pop(0)
        return text, calls, {"role": "assistant", "content": text or "tool use"}

    def tool_results(self, results):
        self.results.append(results)
        return {"role": "user", "content": "results"}


@pytest.fixture
def patched(monkeypatch):
    state = {}

    def install(script, tool=None):
        adapter = FakeAdapter(script)
        state["adapter"] = adapter
        monkeypatch.setattr(
            chat_agent, "make_adapter", lambda *a, **k: ("claude", adapter)
        )
        if tool is not None:
            monkeypatch.setattr(chat_agent.chat_tools, "call_tool", tool)
        return adapter

    state["install"] = install
    return state


def call(*, question="q", conv_id="", **kw):
    return list(
        chat_agent.run_turn(
            app=object(), question=question, api_key="k", conv_id=conv_id, **kw
        )
    )


def ok_tool(app, name, arguments):
    return {"ok": True, "summary": f"{name} ok", "detail": {"x": 1}}


def test_plain_answer_no_tools(patched):
    patched["install"]([("The answer.", [])])
    events = call()
    texts = [e for e in events if e["type"] == "text"]
    assert texts and texts[-1]["delta"] == "The answer."
    assert [e for e in events if e["type"] == "done"]


def test_tool_call_then_answer(patched):
    adapter = patched["install"](
        [
            ("", [{"id": "1", "name": "run_query", "arguments": {"template": "word"}}]),
            ("Done researching.", []),
        ],
        tool=ok_tool,
    )
    events = call()
    kinds = [e["type"] for e in events]
    assert "tool_call" in kinds and "tool_result" in kinds
    assert [e for e in events if e["type"] == "text"][-1]["delta"] == "Done researching."
    # the tool result was handed back to the model
    assert adapter.results and adapter.results[0][0][1]["ok"] is True


def test_tool_budget_is_enforced(patched):
    """Past the cap, no more tools run, but every call still gets a result."""
    script = [
        ("", [{"id": str(i), "name": "run_query", "arguments": {}}]) for i in range(8)
    ]
    script.append(("Final.", []))
    adapter = patched["install"](script, tool=ok_tool)
    events = call(max_tool_calls=3)
    executed = [e for e in events if e["type"] == "tool_call"]
    assert len(executed) == 3, [e["name"] for e in executed]
    done = [e for e in events if e["type"] == "done"][0]
    assert done["tool_calls"] == 3
    # every requested call was answered, including the over-budget ones
    for batch in adapter.results:
        assert len(batch) >= 1
        for _c, payload in batch:
            assert "ok" in payload


def test_over_budget_payload_tells_model_to_stop(patched):
    script = [("", [{"id": str(i), "name": "run_query", "arguments": {}}]) for i in range(4)]
    script.append(("Final.", []))
    adapter = patched["install"](script, tool=ok_tool)
    call(max_tool_calls=1)
    refusals = [
        payload
        for batch in adapter.results
        for _c, payload in batch
        if not payload["ok"]
    ]
    assert refusals, "expected at least one over-budget refusal payload"
    assert "budget" in refusals[0]["summary"].lower()


def test_failing_tool_is_reported_not_raised(patched):
    def boom(app, name, arguments):
        raise RuntimeError("should never escape")

    # call_tool is the thing that swallows exceptions; simulate it having
    # already done so, and separately assert the real one does.
    patched["install"](
        [
            ("", [{"id": "1", "name": "run_query", "arguments": {}}]),
            ("Recovered.", []),
        ],
        tool=lambda a, n, args: {"ok": False, "summary": "Tool failed", "detail": {}},
    )
    events = call()
    result = [e for e in events if e["type"] == "tool_result"][0]
    assert result["ok"] is False
    assert [e for e in events if e["type"] == "text"][-1]["delta"] == "Recovered."


def test_provider_error_becomes_error_event(patched, monkeypatch):
    class Boom:
        def turn(self, messages):
            raise RuntimeError("network down")

    monkeypatch.setattr(chat_agent, "make_adapter", lambda *a, **k: ("claude", Boom()))
    events = call()
    assert events[-1]["type"] == "error"
    assert "network down" in events[-1]["message"]


def test_narration_is_not_the_answer(patched):
    patched["install"](
        [
            ("Let me check.", [{"id": "1", "name": "run_query", "arguments": {}}]),
            ("The real answer.", []),
        ],
        tool=ok_tool,
    )
    events = call()
    notes = [e for e in events if e["type"] == "note"]
    texts = [e for e in events if e["type"] == "text"]
    assert notes and notes[0]["text"] == "Let me check."
    assert len(texts) == 1 and texts[0]["delta"] == "The real answer."


def test_missing_question_and_key():
    events = list(
        chat_agent.run_turn(app=object(), question="", api_key="k")
    )
    assert events[0]["type"] == "error"
    events = list(
        chat_agent.run_turn(app=object(), question="q", api_key="")
    )
    assert events[0]["type"] == "error"


def test_unknown_provider():
    events = list(
        chat_agent.run_turn(
            app=object(), question="q", api_key="k", provider="gpt"
        )
    )
    assert events[0]["type"] == "error"
    assert "Unknown provider" in events[0]["message"]


def test_history_is_kept_and_reset(patched):
    patched["install"]([("A.", [])])
    call(conv_id="c1")
    assert chat_agent.get_history("c1")
    chat_agent.reset_conversation("c1")
    assert chat_agent.get_history("c1") == []


def test_history_cap(patched):
    patched["install"]([("A.", [])] * 1)
    chat_agent.set_history("c2", [{"role": "user", "content": str(i)} for i in range(200)])
    assert len(chat_agent.get_history("c2")) == chat_agent.HISTORY_LIMIT


def test_conversation_store_evicts():
    for i in range(chat_agent.CONVERSATION_LIMIT + 10):
        chat_agent.set_history(f"conv{i}", [{"role": "user", "content": "x"}])
    assert len(chat_agent._CONVERSATIONS) <= chat_agent.CONVERSATION_LIMIT


def test_describe_call_titles():
    title, inputs = chat_agent.describe_call("aggregate", {
        "template": "word sp=verb", "column": 1, "feature": "vs"
    })
    assert "vs" in title
    assert any(label == "Query" for label, _ in inputs)
    # unknown tool still renders sensibly
    title, _ = chat_agent.describe_call("some_new_tool", {"a": 1})
    assert title == "Some new tool"


def test_tool_schemas_wellformed():
    names = set()
    for schema in chat_agent.TOOL_SCHEMAS:
        assert schema["name"] not in names
        names.add(schema["name"])
        assert schema["description"]
        params = schema["parameters"]
        assert params["type"] == "object"
        for req in params.get("required", []):
            assert req in params["properties"], (schema["name"], req)
    from tf.browser import chat_tools

    assert names == set(chat_tools.TOOLS), "schemas and implementations disagree"


class TestEpistemicHonesty:
    """The prompt must actually carry the limits guidance.

    These are cheap guards against someone trimming the system prompt
    later and quietly losing the "say what you could not establish"
    behaviour, which is invisible until an answer is confidently wrong.
    """

    def test_names_what_the_corpus_cannot_settle(self):
        prompt = chat_agent.SYSTEM_PROMPT.lower()
        for topic in (
            "meaning",
            "dating",
            "text critic",
            "etymolog",
            "coreference",
            "intertextual",
            "cantillation",
        ):
            assert topic in prompt, f"prompt no longer mentions {topic}"

    def test_requires_marking_inference_vs_count(self):
        prompt = chat_agent.SYSTEM_PROMPT.lower()
        assert "inference" in prompt
        assert "guess" in prompt
        assert "epistemic status" in prompt

    def test_warns_that_zero_results_is_ambiguous(self):
        assert "zero results is ambiguous" in chat_agent.SYSTEM_PROMPT.lower()

    def test_asks_for_the_caveat_blockquote(self):
        assert "> " in chat_agent.SYSTEM_PROMPT
        assert "blockquote" in chat_agent.SYSTEM_PROMPT.lower()

    def test_says_etcbc_analysis_is_a_model_not_fact(self):
        prompt = chat_agent.SYSTEM_PROMPT.lower()
        assert "one linguistic model" in prompt or "not neutral" in prompt


class TestConfigurableBudget:
    def test_ceiling_is_defined_and_above_default(self):
        assert chat_agent.TOOL_CALL_CEILING > chat_agent.MAX_TOOL_CALLS

    def test_higher_budget_allows_more_calls(self, patched):
        script = [
            ("", [{"id": str(i), "name": "run_query", "arguments": {}}])
            for i in range(25)
        ]
        script.append(("Final.", []))
        patched["install"](script, tool=ok_tool)
        events = call(max_tool_calls=20)
        executed = [e for e in events if e["type"] == "tool_call"]
        assert len(executed) == 20
        assert [e for e in events if e["type"] == "done"][0]["tool_calls"] == 20

    def test_budget_of_one(self, patched):
        script = [
            ("", [{"id": str(i), "name": "run_query", "arguments": {}}])
            for i in range(5)
        ]
        script.append(("Final.", []))
        patched["install"](script, tool=ok_tool)
        events = call(max_tool_calls=1)
        assert len([e for e in events if e["type"] == "tool_call"]) == 1
        assert [e for e in events if e["type"] == "done"]

    def test_turn_limit_scales_with_budget(self, patched):
        """A large budget must not be cut short by a fixed turn cap."""
        script = [
            ("", [{"id": str(i), "name": "run_query", "arguments": {}}])
            for i in range(30)
        ]
        script.append(("Final.", []))
        patched["install"](script, tool=ok_tool)
        events = call(max_tool_calls=30)
        assert len([e for e in events if e["type"] == "tool_call"]) == 30
