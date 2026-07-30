"""
AI query generation for the Text-Fabric BHSA browser.

Natural language -> Text-Fabric search template, as a closed loop:

1. Look up candidate lexemes for the content words of the request in the
   corpus lexeme database (English gloss, ETCBC transliteration, or
   Hebrew script) and inject them into the prompt.
2. Ask the LLM for a search template.
3. Validate the template deterministically against the corpus inventory
   (`query_validator`), catching wrong feature values and lexemes that
   Text-Fabric itself would silently accept with zero results.
4. Execute the template against the live corpus.  Parse errors and
   zero-result diagnoses are fed back to the LLM, which retries — up to
   `MAX_ATTEMPTS` rounds.

Providers: Google Gemini (API key from the UI or GEMINI_API_KEY) or
Anthropic Claude (keys starting with `sk-ant`, or ANTHROPIC_API_KEY).
"""

import os
import re

from .corpus_data import search_lexemes
from .query_validator import validate_query

MAX_ATTEMPTS = 4
RESULT_CAP = 100000  # stop counting beyond this many results
ZERO_PROBE_CAP = 8  # max relaxation probes when diagnosing zero results

# Optional hard overrides; when unset, Gemini's best available model is
# resolved from the API's model list at call time (Google retires model
# ids regularly — gemini-2.5-pro is already closed to new users).
GEMINI_MODEL = os.environ.get("AI_QUERY_GEMINI_MODEL", "")
GEMINI_FALLBACK_MODEL = "gemini-3.6-flash"  # newest GA model as of 2026-07
ANTHROPIC_MODEL = os.environ.get("AI_QUERY_ANTHROPIC_MODEL", "claude-sonnet-5")

# Custom endpoints (proxies, gateways, self-hosted relays).  A request
# may override these per call; these are the server-wide defaults.
GEMINI_BASE_URL = os.environ.get("AI_QUERY_GEMINI_BASE_URL", "")
ANTHROPIC_BASE_URL = os.environ.get("AI_QUERY_ANTHROPIC_BASE_URL", "")

PROVIDERS = ("gemini", "claude")

_GEMINI_RESOLVED = None


def detect_provider(api_key):
    """Infer the provider from the shape of the key."""
    return "claude" if api_key.startswith("sk-ant") else "gemini"

_TEMPLATE_CACHE = None

STOPWORDS = set(
    """a an and are as at be but by for from has have i in is it me my of on or
    show showing that the their them then there these this those to want was we
    were where which who whose will with you your all any each also only its
    it's don't doesn't not no non containing contains contain occur occurs
    occurrences instance instances example examples list find search query
    queries
    word words verb verbs noun nouns adjective adjectives preposition
    prepositions particle particles pronoun pronouns suffix suffixes clause
    clauses phrase phrases sentence sentences verse verses chapter chapters
    book books lexeme lexemes form forms state stem stems tense person gender
    number singular plural dual masculine feminine absolute construct perfect
    imperfect imperative infinitive participle wayyiqtol qatal yiqtol qal
    niphal nifal piel pual hiphil hifil hophal hofal hithpael hitpael subject
    object predicate complement direct speech narrative followed immediately
    before after between first second third same different every without
    hebrew aramaic bible biblical""".split()
)


# ----------------------------------------------------------------------------
# prompt building
# ----------------------------------------------------------------------------


def build_system_prompt():
    """Load the v3 production prompt template."""
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is None:
        path = os.path.join(os.path.dirname(__file__), "ai_prompt_template_v3.md")
        with open(path, encoding="utf-8") as fh:
            _TEMPLATE_CACHE = fh.read()
    return _TEMPLATE_CACHE


def extract_terms(user_input):
    """Candidate content words to look up in the lexeme database."""
    terms = []
    terms.extend(re.findall(r'"([^"]+)"', user_input))
    terms.extend(re.findall(r"'([^']+)'", user_input))
    terms.extend(re.findall(r"[֐-תװ-״]+", user_input))
    for word in re.findall(r"[A-Za-z][A-Za-z'-]+", user_input):
        lowered = word.lower().strip("'-")
        if len(lowered) >= 3 and lowered not in STOPWORDS:
            terms.append(lowered)
    seen = set()
    unique = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def find_lexemes(user_input, per_term=4, cap=30):
    """Look up lexeme candidates for the request; returns list of dicts."""
    found = []
    seen = set()
    for term in extract_terms(user_input):
        for entry in search_lexemes(term, max_results=per_term):
            key = (entry["lex"], entry["lang"])
            if key not in seen:
                seen.add(key)
                found.append(entry)
        if len(found) >= cap:
            break
    return found[:cap]


def format_lexemes(lexemes):
    if not lexemes:
        return (
            "(No matching lexemes found — rely on `gloss` constraints "
            "rather than guessing transliterations.)"
        )
    lines = []
    for e in lexemes:
        lang = f", {e['lang']}" if e["lang"] != "Hebrew" else ""
        lines.append(
            f"- {e['gloss']}: lex={e['lex']} ({e['sp']}, {e['freq']}×"
            f"{lang}) {e['voc']}"
        )
    return "\n".join(lines)


def build_prompt(user_input, lexemes, feedback_history):
    prompt = build_system_prompt()
    prompt = prompt.replace("{LEXEMES_PLACEHOLDER}", format_lexemes(lexemes))
    prompt = prompt.replace("{USER_PROMPT}", user_input)
    for attempt, feedback in feedback_history:
        prompt += (
            f"\n\n---\n\n## PREVIOUS ATTEMPT (rejected)\n\n"
            f"```\n{attempt}\n```\n\n"
            f"## FEEDBACK FROM THE CORPUS ENGINE\n\n{feedback}\n\n"
            f"Produce a corrected template (template only, no commentary)."
        )
    return prompt


# ----------------------------------------------------------------------------
# LLM providers
# ----------------------------------------------------------------------------


def _resolve_gemini_model(genai):
    """
    Pick the best generateContent model the key can actually use.

    Preference: newest version first, then pro > flash > flash-lite.
    Specialized variants (image/tts/live/preview/...) are excluded by the
    name pattern.  Falls back to GEMINI_FALLBACK_MODEL if listing fails.
    """
    global _GEMINI_RESOLVED
    if GEMINI_MODEL:
        return GEMINI_MODEL
    if _GEMINI_RESOLVED:
        return _GEMINI_RESOLVED
    best, bestKey = None, None
    try:
        for m in genai.list_models():
            name = m.name.split("/")[-1]
            if "generateContent" not in getattr(
                m, "supported_generation_methods", []
            ):
                continue
            match = re.fullmatch(r"gemini-(\d+(?:\.\d+)?)-(pro|flash)(-lite)?", name)
            if not match:
                continue
            tier = {"pro": 3, "flash": 2}[match.group(2)]
            if match.group(3):
                tier -= 1
            key = (float(match.group(1)), tier)
            if bestKey is None or key > bestKey:
                bestKey, best = key, name
    except Exception:
        pass
    _GEMINI_RESOLVED = best or GEMINI_FALLBACK_MODEL
    return _GEMINI_RESOLVED


def _call_gemini(prompt, api_key, model="", base_url=""):
    global _GEMINI_RESOLVED
    import google.generativeai as genai

    clientOptions = {}
    base_url = base_url or GEMINI_BASE_URL
    if base_url:
        clientOptions["api_endpoint"] = base_url.replace("https://", "").replace(
            "http://", ""
        ).rstrip("/")
    genai.configure(api_key=api_key, client_options=clientOptions or None)
    modelName = model or _resolve_gemini_model(genai)
    try:
        response = _gemini_generate(genai, modelName, prompt)
    except Exception as e:
        # Model ids get retired; re-resolve once with the fallback (only
        # when the model was auto-picked, not explicitly requested).
        if (
            not model
            and modelName != GEMINI_FALLBACK_MODEL
            and (
                "404" in str(e)
                or "not found" in str(e).lower()
                or "no longer available" in str(e).lower()
            )
        ):
            _GEMINI_RESOLVED = GEMINI_FALLBACK_MODEL
            response = _gemini_generate(genai, GEMINI_FALLBACK_MODEL, prompt)
        else:
            raise
    if not response.candidates:
        raise RuntimeError("Gemini returned no candidates (safety block?)")
    finish = getattr(response.candidates[0], "finish_reason", 1)
    if finish == 3:
        raise RuntimeError("Gemini blocked the response (safety)")
    return response.text


def _gemini_generate(genai, modelName, prompt):
    model = genai.GenerativeModel(modelName)
    return model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1, max_output_tokens=4096
        ),
        safety_settings=[
            {"category": cat, "threshold": "BLOCK_NONE"}
            for cat in (
                "HARM_CATEGORY_HARASSMENT",
                "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "HARM_CATEGORY_DANGEROUS_CONTENT",
            )
        ],
    )


def _call_anthropic(prompt, api_key, model="", base_url=""):
    import anthropic

    base_url = base_url or ANTHROPIC_BASE_URL
    client = anthropic.Anthropic(
        api_key=api_key, **({"base_url": base_url} if base_url else {})
    )
    response = client.messages.create(
        model=model or ANTHROPIC_MODEL,
        max_tokens=4096,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in response.content if block.type == "text"
    )


def call_llm(prompt, api_key, provider="", model="", base_url=""):
    """Dispatch to the selected provider (auto-detected from the key
    shape when not given explicitly)."""
    provider = (provider or "").strip().lower() or detect_provider(api_key)
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unknown provider {provider!r}; expected one of {', '.join(PROVIDERS)}"
        )
    if provider == "claude":
        return _call_anthropic(prompt, api_key, model=model, base_url=base_url)
    return _call_gemini(prompt, api_key, model=model, base_url=base_url)


def strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


# ----------------------------------------------------------------------------
# execution & zero-result diagnosis
# ----------------------------------------------------------------------------


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text):
    return _TAG_RE.sub("", text or "").strip()


def make_executor(app):
    """
    Build an executor closure over a loaded TF advanced app.

    The executor takes (query, limit) and returns (count, ok, messages):
    `ok` False means the template failed to parse/execute; `messages`
    holds Text-Fabric's diagnostics as plain text.
    """
    S = app.api.S

    def executor(query, limit=RESULT_CAP):
        msgs = []
        try:
            # here=False keeps per-search state off the shared S object,
            # which matters because the browser serves requests threaded.
            # It also makes search return a 4-tuple ending in the executor.
            res = S.search(query, limit=limit, here=False, _msgCache=msgs)
        except Exception as e:
            return 0, False, f"Execution error: {e}"
        if isinstance(res, tuple) and len(res) == 4:
            results, status, messages, _exe = res
        elif isinstance(res, tuple) and len(res) == 3:
            results, status, messages = res
        else:
            results, status, messages = res, True, ""
        try:
            count = len(list(results))
        except Exception as e:
            return 0, False, f"Execution error: {e}"
        return count, bool(status), _strip_html(str(messages or ""))

    return executor


def _feature_spec_tokens(line):
    """(atomPrefix, [featureSpec tokens]) for an atom line, else (line, [])."""
    stripped = line.strip()
    if not stripped or stripped.startswith("%") or stripped.startswith("/"):
        return line, []
    tokens = re.split(r"(?<!\\)\s+", stripped)
    specs = [
        t
        for t in tokens[1:]
        if re.match(r"^[A-Za-z0-9_@]+[=#~<>]", t)
    ]
    return tokens[0], specs


def diagnose_zero(query, executor):
    """
    Find which single constraints eliminate all results, by removing one
    feature spec at a time and re-running with limit=1.
    """
    lines = query.split("\n")
    culprits = []
    probes = 0
    for i, line in enumerate(lines):
        _, specs = _feature_spec_tokens(line)
        for spec in specs:
            if probes >= ZERO_PROBE_CAP:
                break
            relaxed = list(lines)
            newLine = line.replace(spec, "", 1).rstrip()
            relaxed[i] = newLine
            probes += 1
            count, ok, _ = executor("\n".join(relaxed), limit=1)
            if ok and count > 0:
                culprits.append((i + 1, spec))
    if not culprits:
        return (
            "The query is syntactically valid but returns 0 results, and no "
            "single constraint is responsible (the combination as a whole "
            "matches nothing). Reconsider the structure — e.g. containment "
            "levels, word order operators, or whether the phenomenon is "
            "expressed with different features."
        )
    listing = "\n".join(
        f"- removing `{spec}` (line {ln}) makes the query match"
        for ln, spec in culprits
    )
    return (
        "The query is syntactically valid but returns 0 results. "
        "Relaxation analysis of single constraints:\n"
        f"{listing}\n"
        "One of these constraints contradicts the rest (wrong value, wrong "
        "node level, or a value that never co-occurs with the others). "
        "Fix or drop the offending constraint."
    )


# ----------------------------------------------------------------------------
# main pipeline
# ----------------------------------------------------------------------------


def generate_query(
    user_prompt,
    api_key,
    executor=None,
    max_attempts=MAX_ATTEMPTS,
    provider="",
    model="",
    base_url="",
):
    """
    Generate a Text-Fabric query from natural language.

    `provider` is "gemini" or "claude" (auto-detected from the key when
    omitted); `model` and `base_url` override the provider defaults.

    Returns a dict with keys: query, explanation, lexemes_used, error,
    result_count, attempts, provider.  `error` is None on success.  When
    `executor` is given (see `make_executor`), the returned query is
    guaranteed to parse, and its result count is reported.
    """
    user_prompt = (user_prompt or "").strip()
    api_key = (api_key or "").strip()
    provider = (provider or "").strip().lower()
    model = (model or "").strip()
    base_url = (base_url or "").strip()
    base = {
        "query": "",
        "explanation": "",
        "lexemes_used": [],
        "error": None,
        "result_count": None,
        "attempts": 0,
        "provider": provider or (detect_provider(api_key) if api_key else ""),
    }
    if not user_prompt:
        return {**base, "error": "Prompt is required"}
    if not api_key:
        return {**base, "error": "API key is required"}
    if provider and provider not in PROVIDERS:
        return {
            **base,
            "error": (
                f"Unknown provider {provider!r}; expected one of "
                f"{', '.join(PROVIDERS)}"
            ),
        }

    lexemes = find_lexemes(user_prompt)
    base["lexemes_used"] = [e["lex"] for e in lexemes]

    feedback_history = []
    query = ""
    zero_retry_used = False

    for attempt in range(1, max_attempts + 1):
        base["attempts"] = attempt
        prompt = build_prompt(user_prompt, lexemes, feedback_history)
        try:
            query = strip_fences(
                call_llm(
                    prompt,
                    api_key,
                    provider=provider,
                    model=model,
                    base_url=base_url,
                )
            )
        except Exception as e:
            return {**base, "error": f"AI provider error: {e}"}
        if not query:
            feedback_history.append(("(empty)", "Your response was empty."))
            continue

        ok, valErrors = validate_query(query)
        if not ok:
            feedback_history.append((query, f"Validation errors:\n{valErrors}"))
            continue

        if executor is None:
            return {
                **base,
                "query": query,
                "explanation": _explanation(lexemes, None, attempt),
            }

        count, execOk, messages = executor(query)
        if not execOk or messages:
            feedback_history.append(
                (query, f"Text-Fabric rejected the template:\n{messages}")
            )
            continue
        if count == 0 and not zero_retry_used:
            zero_retry_used = True
            feedback_history.append((query, diagnose_zero(query, executor)))
            continue
        return {
            **base,
            "query": query,
            "result_count": count,
            "explanation": _explanation(lexemes, count, attempt),
        }

    # Out of attempts: return the last query if it at least validated,
    # with an explanatory error otherwise.
    lastFeedback = feedback_history[-1][1] if feedback_history else ""
    if query and (executor is None or "0 results" in lastFeedback):
        # Query runs but matches nothing — surface it anyway.
        return {
            **base,
            "query": query,
            "result_count": 0,
            "explanation": (
                "The query is valid but matches nothing in the corpus. "
                "The described combination may not occur."
            ),
        }
    return {
        **base,
        "query": query,
        "error": (
            f"Could not produce a working query after {max_attempts} "
            f"attempts. Last feedback:\n{lastFeedback}"
        ),
    }


def _explanation(lexemes, count, attempts):
    parts = []
    if lexemes:
        shown = ", ".join(f"{e['gloss']} ({e['lex']})" for e in lexemes[:3])
        parts.append(f"Lexemes: {shown}")
    if count is not None:
        capNote = "+" if count >= RESULT_CAP else ""
        parts.append(f"{count}{capNote} results in the corpus")
    if attempts > 1:
        parts.append(f"{attempts} attempts")
    return ". ".join(parts)
