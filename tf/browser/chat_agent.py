"""
Research chat agent for the BHSA browser.

Answers linguistic questions about the Hebrew Bible by calling
Text-Fabric as a tool (see `chat_tools`) against the corpus already
loaded in the browser process, then reasoning over what comes back.

The loop is a generator of events, so the web layer can stream tool
calls to the page as they happen rather than making the user wait in
silence:

    for event in run_turn(app, question, ...):
        ...  # {"type": "tool_call" | "tool_result" | "text" | "done" | ...}

Both providers are supported behind one interface: Claude via tool-use
content blocks, Gemini via function calling.  Conversation state lives in
memory, keyed by conversation id, and is lost when the service restarts.
"""

import json
import os
import time
from collections import OrderedDict

from . import chat_tools
from .ai_query import (
    ANTHROPIC_BASE_URL,
    ANTHROPIC_MODEL,
    GEMINI_BASE_URL,
    PROVIDERS,
    _resolve_gemini_model,
    detect_provider,
)

MAX_TOOL_CALLS = int(os.environ.get("AI_CHAT_MAX_TOOL_CALLS", "10"))
# Upper bound the UI may ask for; guards against a runaway loop burning
# the API budget regardless of what the client sends.
TOOL_CALL_CEILING = int(os.environ.get("AI_CHAT_TOOL_CALL_CEILING", "40"))
MAX_TOKENS = 4096
HISTORY_LIMIT = 40  # messages kept per conversation
CONVERSATION_LIMIT = 50  # conversations kept in memory

_CONVERSATIONS = OrderedDict()


# ---------------------------------------------------------------------------
# tool schemas
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "search_lexemes",
        "description": (
            "Find Hebrew/Aramaic lexemes by English gloss, ETCBC "
            "transliteration, or Hebrew script. Use this before writing any "
            "query that mentions a specific word — never guess a "
            "transliteration. Returns the exact `lex` value to use, with "
            "corpus frequency and all senses."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": (
                        "English gloss (e.g. 'give'), ETCBC transliteration "
                        "(e.g. 'NTN'), or Hebrew (e.g. 'נתן')."
                    ),
                }
            },
            "required": ["term"],
        },
    },
    {
        "name": "run_query",
        "description": (
            "Execute a Text-Fabric search template against BHSA. Returns the "
            "total number of results and a small sample with references and "
            "text. Use it to find and inspect occurrences. If you need "
            "proportions ('always', 'usually', 'never'), use `aggregate` "
            "instead — do not infer frequency from a sample."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "template": {
                    "type": "string",
                    "description": (
                        "Text-Fabric search template. Indentation means "
                        "containment; relations between named atoms go on "
                        "their own lines."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "How many sample rows to return (max 20).",
                },
            },
            "required": ["template"],
        },
    },
    {
        "name": "aggregate",
        "description": (
            "THE tool for 'always / usually / never' questions. Runs a query "
            "and returns the distribution of a feature over one column of the "
            "results, with counts and percentages over ALL results (not a "
            "sample). Example: to find what follows a word, write a query "
            "whose column 3 is the following word, then aggregate `lex` over "
            "column 3."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "template": {"type": "string", "description": "Search template."},
                "column": {
                    "type": "integer",
                    "description": (
                        "Which result column to aggregate over, 1-based. "
                        "Columns follow the order the atoms appear in the "
                        "template; atoms inside quantifiers do not count."
                    ),
                },
                "feature": {
                    "type": "string",
                    "description": "Feature to tabulate, e.g. lex, sp, vs, vt.",
                },
            },
            "required": ["template", "column", "feature"],
        },
    },
    {
        "name": "get_passage",
        "description": (
            "Read a passage with full morphology for every word. Use it to "
            "check how a word behaves in context before making a claim. Book "
            "names here are ENGLISH (Genesis, Numbers, Isaiah, 1_Samuel)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "book": {"type": "string", "description": "English book name."},
                "chapter": {"type": "integer"},
                "verse": {"type": "integer"},
                "end_verse": {
                    "type": "integer",
                    "description": "Optional last verse of a range (max 10).",
                },
            },
            "required": ["book", "chapter", "verse"],
        },
    },
    {
        "name": "lexeme_profile",
        "description": (
            "Overview of how a lexeme behaves across the whole corpus: "
            "occurrences, senses, verbal stem and tense distribution, which "
            "books it clusters in, and sample references. The natural first "
            "step for 'how is this word used' questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "lex": {
                    "type": "string",
                    "description": (
                        "Exact ETCBC lexeme including its suffix mark, e.g. "
                        "NTN[ or MLK/. Get it from search_lexemes first."
                    ),
                }
            },
            "required": ["lex"],
        },
    },
    {
        "name": "list_feature_values",
        "description": (
            "The valid values of a BHSA feature with their counts. Use when "
            "unsure whether a value exists — a wrong value silently returns "
            "zero results rather than an error."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "feature": {
                    "type": "string",
                    "description": "Feature name, e.g. sp, vs, vt, function.",
                }
            },
            "required": ["feature"],
        },
    },
]


SYSTEM_PROMPT = """\
You are a research assistant for the Hebrew Bible, working with the BHSA corpus \
(ETCBC) through Text-Fabric. You answer linguistic questions by querying the \
corpus and reasoning over real results — never from memory alone.

## Method

1. Resolve any word mentioned in the question with `search_lexemes` before using \
it in a query. Lexeme values are case-sensitive and carry suffix marks: verbs \
end in `[`, nouns in `/`, further homonyms add `=`. Never invent one.
2. For "how is X used" / "what does X mean", start with `lexeme_profile`.
3. For "always / usually / never / how often", you MUST use `aggregate`. A \
sample of 20 rows tells you nothing about proportions. Report the actual counts \
and percentages.
4. Read real passages with `get_passage` when you want to show or check how \
something behaves in context.
5. If a query returns 0 results, that is evidence only if the query was right. \
Check your feature values with `list_feature_values` before concluding a \
construction never occurs.

## Answering

- Cite specific references (Genesis 1:1) for every claim about usage. Quote the \
Hebrew when it helps.
- Give numbers: "7 of 380 occurrences (1.8%)", not "rarely".
- Correct the premise of a question when the data contradicts it, and say so \
plainly — "no, and here is the actual distribution" is a good answer.
- Be concise and scholarly. No preamble, no restating the question. Markdown for \
structure; keep it tight.

## Limits — be explicit about what you actually established

The corpus can settle some questions and not others, and the difference matters \
more than a confident tone. Never present an educated guess as a finding.

**What BHSA can settle:** morphology (stem, tense, person, gender, number, \
state), the syntactic analysis ETCBC assigned (phrase function, clause type, \
mother relations), word order and adjacency, lexeme frequency and distribution, \
ketiv/qere, and roots.

**What it cannot settle, because the data is simply not there:**
- *Meaning.* `gloss` is a single contextless label per lexeme, not a sense \
inventory. There is no semantic domain, no metaphor or connotation annotation, \
no sense disambiguation. Distributional evidence constrains meaning; it does not \
determine it.
- *Dating and diachrony.* There are no date features, and book order is not \
chronology. You cannot show a usage is "early" or "late".
- *Text criticism.* This is the Leningrad Codex with Masoretic vocalization. \
There is no apparatus, no LXX, no Qumran, no variants beyond ketiv/qere.
- *Etymology and cognates.* Absent entirely.
- *Reference tracking.* No coreference or anaphora annotation — you cannot ask \
who a pronoun refers to.
- *Intertextuality.* Allusions, quotations and parallels are not annotated.
- *Cantillation.* Accents are present in the text but carry no analytic features.
- *Authorial intent, theology, genre.* Not encoded.

Also keep in mind, and say so when it bears on the answer:
- ETCBC's syntactic labels are one linguistic model's analysis, not neutral \
fact. Another framework would segment some of it differently.
- A count is only as good as the query that produced it. State how you \
operationalized the question, because a different template gives a different \
number.
- Zero results is ambiguous: it means the construction does not occur *only if* \
the query was right. Verify feature values before treating absence as evidence.
- Lexeme boundaries and homonym splits (the `=` markers) are lexicographic \
decisions made by the editors.

**So, in every answer, make the epistemic status obvious:**
- Say which parts are counted from the corpus and which are your inference.
- When the honest answer is a well-grounded guess, call it that, and give the \
reasoning that supports it rather than dressing it up as a result.
- When the question cannot be answered from BHSA at all, say so directly, \
explain why the data cannot reach it, give whatever partial evidence the corpus \
does offer, and name what would actually settle it (a lexicon such as HALOT or \
DCH, the versions, comparative Semitic data, secondary literature).
- If the tool budget ran out before you were confident, say what you found, what \
is still open, and which query would resolve it.

End with a one-line `> ` blockquote stating the basis and the main limitation, \
whenever the answer involves interpretation, an incomplete search, or a question \
the corpus cannot fully reach. Skip it only when the answer is a plain counted \
fact.

## Query syntax essentials

Indentation = containment. Named atoms (`w1:word`) can be related on their own \
lines: `w1 <: w2` (w1 immediately before w2), `w1 << w2` (before, anywhere), \
`w1 .gn=gn. w2` (same gender). Quantifiers `/without/`, `/where/../have/`, \
`/with/../or/` sit at exactly the indentation of the atom they modify, \
immediately after it, and end with `/-/`.

Word features: sp (verb, subs, nmpr, adjv, advb, prep, conj, art, prps, nega...), \
vs (qal, nif, piel, pual, hif, hof, hit; Aramaic peal, pael, afel...), vt (perf, \
impf, wayq, impv, infc, infa, ptca, ptcp), gn (m/f), nu (sg/pl/du), ps (p1/p2/p3), \
st (a/c/e), lex, gloss, freq_lex. Phrase: function (Pred, Subj, Objc, Cmpl, \
PreC...), typ (VP, NP, PP, CP...). Clause: kind (VC/NC/WP), typ, domain (N/Q/D), \
rela.

Note `NA` and `unknown` are real values, not blanks: `gn=m|f` to demand real gender.

In queries, `book=` takes the LATIN name (Genesis, Numeri, Jesaia, Psalmi, \
Chronica_I) or use `book@en=` for English. In `get_passage`, book names are English.
"""


# ---------------------------------------------------------------------------
# conversation store
# ---------------------------------------------------------------------------


def get_history(conv_id):
    if not conv_id:
        return []
    history = _CONVERSATIONS.get(conv_id)
    if history is None:
        return []
    _CONVERSATIONS.move_to_end(conv_id)
    return history


def set_history(conv_id, messages):
    if not conv_id:
        return
    # Never store a turn whose tool calls were left unanswered; replaying
    # one is an API error that would break the whole conversation.
    messages = _drop_dangling_tool_calls(list(messages))
    _CONVERSATIONS[conv_id] = messages[-HISTORY_LIMIT:]
    _CONVERSATIONS.move_to_end(conv_id)
    while len(_CONVERSATIONS) > CONVERSATION_LIMIT:
        _CONVERSATIONS.popitem(last=False)


def reset_conversation(conv_id):
    _CONVERSATIONS.pop(conv_id, None)


# ---------------------------------------------------------------------------
# provider adapters
#
# Each adapter turns one model turn into: (text, [tool calls], raw messages to
# append to history).  A tool call is {"id", "name", "arguments"}.
# ---------------------------------------------------------------------------


class ClaudeAdapter:
    def __init__(self, api_key, model="", base_url=""):
        import anthropic

        base = base_url or ANTHROPIC_BASE_URL
        self.client = anthropic.Anthropic(
            api_key=api_key, **({"base_url": base} if base else {})
        )
        self.model = model or ANTHROPIC_MODEL

    def tools(self):
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["parameters"],
            }
            for t in TOOL_SCHEMAS
        ]

    def turn(self, messages):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=self.tools(),
            messages=messages,
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        calls = [
            {"id": block.id, "name": block.name, "arguments": block.input}
            for block in response.content
            if block.type == "tool_use"
        ]
        assistant = {
            "role": "assistant",
            "content": [block.model_dump() for block in response.content],
        }
        return text, calls, assistant

    def tool_results(self, results):
        """results: list of (call, payload) -> one user message."""
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": call["id"],
                    "content": json.dumps(payload)[:20000],
                    "is_error": not payload.get("ok", True),
                }
                for call, payload in results
            ],
        }


class GeminiAdapter:
    def __init__(self, api_key, model="", base_url=""):
        import google.generativeai as genai

        clientOptions = {}
        base = base_url or GEMINI_BASE_URL
        if base:
            clientOptions["api_endpoint"] = (
                base.replace("https://", "").replace("http://", "").rstrip("/")
            )
        genai.configure(api_key=api_key, client_options=clientOptions or None)
        self.genai = genai
        self.model_name = model or _resolve_gemini_model(genai)

    def _tool_config(self):
        return [
            {
                "function_declarations": [
                    {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"],
                    }
                    for t in TOOL_SCHEMAS
                ]
            }
        ]

    def turn(self, messages):
        model = self.genai.GenerativeModel(
            self.model_name,
            system_instruction=SYSTEM_PROMPT,
            tools=self._tool_config(),
        )
        response = model.generate_content(
            messages,
            generation_config=self.genai.types.GenerationConfig(
                temperature=0.2, max_output_tokens=MAX_TOKENS
            ),
        )
        text = ""
        calls = []
        parts = []
        for candidate in response.candidates or []:
            for part in candidate.content.parts:
                parts.append(part)
                if getattr(part, "text", ""):
                    text += part.text
                fn = getattr(part, "function_call", None)
                if fn and fn.name:
                    calls.append(
                        {
                            "id": f"{fn.name}-{len(calls)}",
                            "name": fn.name,
                            "arguments": dict(fn.args or {}),
                        }
                    )
        assistant = {"role": "model", "parts": parts}
        return text, calls, assistant

    def tool_results(self, results):
        return {
            "role": "user",
            "parts": [
                {
                    "function_response": {
                        "name": call["name"],
                        "response": payload,
                    }
                }
                for call, payload in results
            ],
        }


def make_adapter(provider, api_key, model="", base_url=""):
    provider = (provider or "").strip().lower() or detect_provider(api_key)
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unknown provider {provider!r}; expected one of {', '.join(PROVIDERS)}"
        )
    if provider == "claude":
        return "claude", ClaudeAdapter(api_key, model=model, base_url=base_url)
    return "gemini", GeminiAdapter(api_key, model=model, base_url=base_url)


def _user_message(provider, text):
    if provider == "gemini":
        return {"role": "user", "parts": [{"text": text}]}
    return {"role": "user", "content": text}


def _assistant_message(provider, text):
    if provider == "gemini":
        return {"role": "model", "parts": [{"text": text}]}
    return {"role": "assistant", "content": text}


def rebuild_history(provider, transcript, limit=12):
    """
    Rebuild conversation context from the browser's transcript.

    Server-side history lives in memory and does not survive a restart,
    but the browser keeps the visible transcript.  When the server has
    forgotten a conversation the client replays it here, so continuing an
    older conversation still works.

    Only the plain text of each turn is restored — tool calls are
    deliberately dropped, since a tool_use block without its matching
    tool_result is rejected by the API.  The model loses the detail of
    how it answered before, but keeps the thread of the conversation.
    """
    messages = []
    if not isinstance(transcript, list):
        return messages
    for entry in transcript[-limit:]:
        if not isinstance(entry, dict):
            continue
        role = entry.get("role")
        text = (entry.get("text") or "").strip()
        if not text:
            continue
        if role == "user":
            messages.append(_user_message(provider, text[:4000]))
        elif role == "assistant":
            messages.append(_assistant_message(provider, text[:4000]))
    # Providers expect turns to alternate and to start with the user.
    while messages and messages[0].get("role") != "user":
        messages.pop(0)
    return messages


def _drop_dangling_tool_calls(messages):
    """
    Remove a trailing assistant turn whose tool calls were never answered.

    If a turn is interrupted part-way — the user presses Stop, or the
    provider errors between the request and the results — the stored
    messages can end with tool calls that have no matching results.
    Replaying that on the next question is an API error, so trim it
    before saving.  Shape-based so it covers both providers.
    """
    while messages:
        last = messages[-1]
        role = last.get("role")
        if role not in ("assistant", "model"):
            break
        content = last.get("content")
        hasCalls = isinstance(content, list) and any(
            isinstance(block, dict) and block.get("type") == "tool_use"
            for block in content
        )
        if not hasCalls:
            hasCalls = any(
                getattr(part, "function_call", None)
                for part in (last.get("parts") or [])
                if not isinstance(part, dict)
            )
        if hasCalls:
            messages.pop()
            continue
        break
    return messages


# ---------------------------------------------------------------------------
# presentation helpers
# ---------------------------------------------------------------------------


def describe_call(name, arguments):
    """Plain-language title for a tool chip, with the inputs to show."""
    args = arguments if isinstance(arguments, dict) else {}
    if name == "search_lexemes":
        return f"Looking up “{args.get('term', '')}”", [
            ("Term", str(args.get("term", "")))
        ]
    if name == "run_query":
        return "Running a corpus query", [
            ("Query", str(args.get("template", "")))
        ]
    if name == "aggregate":
        return (
            f"Counting {args.get('feature', '')} across all results",
            [
                ("Query", str(args.get("template", ""))),
                ("Column", str(args.get("column", ""))),
                ("Feature", str(args.get("feature", ""))),
            ],
        )
    if name == "get_passage":
        ref = f"{args.get('book', '')} {args.get('chapter', '')}:{args.get('verse', '')}"
        if args.get("end_verse"):
            ref += f"–{args['end_verse']}"
        return f"Reading {ref}", [("Passage", ref)]
    if name == "lexeme_profile":
        return f"Profiling {args.get('lex', '')}", [("Lexeme", str(args.get("lex", "")))]
    if name == "list_feature_values":
        return (
            f"Checking values of {args.get('feature', '')}",
            [("Feature", str(args.get("feature", "")))],
        )
    pretty = name.replace("_", " ").strip()
    return pretty[:1].upper() + pretty[1:], [
        (k, str(v)) for k, v in list(args.items())[:4]
    ]


# ---------------------------------------------------------------------------
# the loop
# ---------------------------------------------------------------------------


def run_turn(
    app,
    question,
    api_key,
    conv_id="",
    provider="",
    model="",
    base_url="",
    max_tool_calls=MAX_TOOL_CALLS,
    transcript=None,
):
    """
    Answer one question, yielding events as the work happens.

    Event types: status, tool_call, tool_result, text, done, error.
    """
    started = time.time()
    question = (question or "").strip()
    api_key = (api_key or "").strip()
    if not question:
        yield {"type": "error", "message": "Question is required"}
        return
    if not api_key:
        yield {"type": "error", "message": "API key is required"}
        return

    try:
        providerName, adapter = make_adapter(
            provider, api_key, model=model, base_url=base_url
        )
    except ValueError as e:
        yield {"type": "error", "message": str(e)}
        return
    except ImportError as e:
        yield {
            "type": "error",
            "message": (
                f"The SDK for this provider is not installed on the server: {e}"
            ),
        }
        return

    messages = list(get_history(conv_id))
    if not messages and transcript:
        # The server forgot this conversation (most likely it restarted);
        # rebuild what context we can from the browser's transcript.
        messages = rebuild_history(providerName, transcript)
        if messages:
            yield {"type": "status", "phase": "restored context"}
    messages.append(_user_message(providerName, question))

    toolCallCount = 0
    answer = ""

    # Each turn may batch several calls, so the turn limit only has to
    # exceed the budget: two spare turns cover the final answer and the
    # one where the model is told the budget is spent.
    maxTurns = max(3, max_tool_calls + 2)

    for _turn in range(maxTurns):
        yield {"type": "status", "phase": "thinking"}
        try:
            text, calls, assistantMessage = adapter.turn(messages)
        except Exception as e:
            yield {"type": "error", "message": f"AI provider error: {e}"}
            return

        messages.append(assistantMessage)

        if text and calls:
            # Narration the model wrote before acting. Not the answer.
            yield {"type": "note", "text": text}
        elif text:
            answer = text

        if not calls:
            break

        # Every requested call must come back with a result: Claude rejects
        # an assistant turn whose tool_use blocks are left unanswered. So a
        # call over budget is still answered — with a refusal payload.
        results = []
        for call in calls:
            overBudget = toolCallCount >= max_tool_calls
            title, inputs = describe_call(call["name"], call["arguments"])
            if overBudget:
                payload = {
                    "ok": False,
                    "summary": "Tool budget exhausted",
                    "detail": {
                        "error": (
                            f"The limit of {max_tool_calls} tool calls for this "
                            "question has been reached. Do not call any more "
                            "tools. Answer now with what you have, and state "
                            "plainly what remains uncertain and which query "
                            "would settle it."
                        )
                    },
                }
            else:
                toolCallCount += 1
                yield {
                    "type": "tool_call",
                    "id": call["id"],
                    "name": call["name"],
                    "title": title,
                    "inputs": [{"label": k, "value": v} for k, v in inputs],
                }
                payload = chat_tools.call_tool(
                    app, call["name"], call["arguments"]
                )
            results.append((call, payload))
            if overBudget:
                continue
            event = {
                "type": "tool_result",
                "id": call["id"],
                "name": call["name"],
                "ok": bool(payload.get("ok", False)),
                "summary": payload.get("summary", ""),
                "detail": payload.get("detail", {}),
            }
            template = (payload.get("detail") or {}).get("template")
            if template:
                event["template"] = template
            yield event

        messages.append(adapter.tool_results(results))
        # A safe point: every tool call now has its result. Save here so
        # an interrupted turn (Stop, a dropped connection) still leaves
        # the conversation intact for the next question.
        set_history(conv_id, messages)

    if not answer:
        answer = (
            "I could not reach a conclusion within the tool budget for this "
            "question. Try narrowing it, or ask about one construction at a time."
        )
    yield {"type": "text", "delta": answer}

    set_history(conv_id, messages)
    yield {
        "type": "done",
        "tool_calls": toolCallCount,
        "seconds": round(time.time() - started, 1),
        "provider": providerName,
    }
