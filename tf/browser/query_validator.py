"""
Deterministic validator for Text-Fabric search templates against the
BHSA corpus inventory.

Text-Fabric itself reports syntax errors (wrong quantifier placement,
unknown features) but silently returns zero results for wrong feature
*values* (`vs=hith`, `lex=NTN` without the `[` marker).  This validator
catches that class of error before a query is ever executed, and offers
did-you-mean suggestions suitable for feeding back to an LLM or showing
to a user.
"""

import difflib
import re

from .corpus_data import (
    all_lexemes,
    edge_features,
    feature_info,
    feature_names,
    lexeme_variants,
    node_types,
)

QUANT_KEYWORDS = {"/without/", "/where/", "/have/", "/with/", "/or/", "/-/"}

# Relation operators between named atoms.  k-nearness forms like <3: are
# matched by the regexes below.
RELATION_OP = re.compile(
    r"""^(
        =|\#|<|>|            # node comparison
        ==|\&\&|\#\#|\|\||   # slot set comparison
        \[\[|\]\]|<<|>>|
        <:|:>|=:|:=|::|
        <\d+:|:\d+>|=\d+:|:\d+=|:\d+:|      # k-nearness
        \.[A-Za-z0-9_@]+\.|                  # .f.
        \.[A-Za-z0-9_@]+[=\#<>][A-Za-z0-9_@]+\.|   # .f=g. etc
        \.[A-Za-z0-9_@]+~.*~[A-Za-z0-9_@]+\.       # .f~re~g.
    )$""",
    re.X,
)
EDGE_REL = re.compile(r"^(-|<)([A-Za-z0-9_@]+)(.*?)(>|-)$")

# Frequent LLM mistakes: wrong feature names with obvious intent.
FEATURE_ALIASES = {
    "pos": "sp",
    "gender": "gn",
    "number": "nu",
    "person": "ps",
    "tense": "vt",
    "stem": "vs",
    "state": "st",
    "lexeme": "lex",
    "part_of_speech": "sp",
}

FEATURE_SPEC = re.compile(r"^([A-Za-z0-9_@]+)(\*|\#|=|<|>|~)?(.*)$", re.S)


def _split_values(valueStr):
    """Split a value spec on unescaped pipes; unescape the parts."""
    parts = re.split(r"(?<!\\)\|", valueStr)
    return [
        p.replace("\\ ", " ").replace("\\|", "|").replace("\\\\", "\\") for p in parts
    ]


def _tokenize(line):
    """Split a template line into tokens on unescaped whitespace."""
    return [t for t in re.split(r"(?<!\\)\s+", line.strip()) if t]


def _suggest(value, candidates, n=3):
    return difflib.get_close_matches(value, candidates, n=n, cutoff=0.6)


def _check_feature_spec(token, lineNo, errors):
    m = FEATURE_SPEC.match(token)
    if not m:
        errors.append(f"line {lineNo}: cannot parse feature spec `{token}`")
        return
    name, op, valueStr = m.group(1), m.group(2), m.group(3)
    if op is None and valueStr:
        errors.append(f"line {lineNo}: cannot parse feature spec `{token}`")
        return
    info = feature_info(name)
    if info is None:
        msg = f"line {lineNo}: unknown feature `{name}`"
        if name in FEATURE_ALIASES:
            msg += f" — use `{FEATURE_ALIASES[name]}` instead"
        else:
            close = _suggest(name, feature_names())
            if close:
                msg += f" — did you mean {', '.join(f'`{c}`' for c in close)}?"
        errors.append(msg)
        return
    if op in (None, "*"):
        return
    if op in ("<", ">"):
        if info["type"] != "int":
            errors.append(
                f"line {lineNo}: `{name}` is not an integer feature; "
                f"`<` and `>` only work on integer features"
            )
        elif not valueStr.lstrip("-").isdigit():
            errors.append(
                f"line {lineNo}: `{name}{op}{valueStr}` — value must be an integer"
            )
        return
    if op == "~":
        try:
            re.compile(valueStr)
        except re.error as e:
            errors.append(f"line {lineNo}: invalid regex in `{token}`: {e}")
        if info["type"] == "int":
            errors.append(
                f"line {lineNo}: `{name}` is an integer feature; "
                f"`~` regex only works on string features"
            )
        return
    # op is = or # : validate each value
    if not valueStr:
        return
    for value in _split_values(valueStr):
        _check_value(name, info, value, lineNo, errors)


def _check_value(name, info, value, lineNo, errors):
    if name == "lex":
        lexes = all_lexemes()
        if value in lexes:
            return
        variants = lexeme_variants(value)
        if variants:
            hints = ", ".join(
                f"`{v}` ({lexes[v]['gloss']}, {lexes[v]['freq']}×)" for v in variants
            )
            errors.append(
                f"line {lineNo}: lexeme `{value}` does not exist — "
                f"did you mean {hints}? (verbs end in `[`, nouns in `/`)"
            )
        else:
            close = _suggest(value, list(lexes), n=3)
            hint = (
                " — closest existing lexemes: "
                + ", ".join(f"`{c}` ({lexes[c]['gloss']})" for c in close)
                if close
                else " — look it up by English gloss instead of guessing"
            )
            errors.append(f"line {lineNo}: lexeme `{value}` does not exist{hint}")
        return
    if info["type"] == "int":
        if not value.lstrip("-").isdigit():
            errors.append(
                f"line {lineNo}: `{name}={value}` — `{name}` is an integer feature"
            )
        return
    if info["type"] == "open":
        return
    values = info["values"]
    if value not in values:
        close = _suggest(value, list(values))
        msg = f"line {lineNo}: `{name}={value}` — `{value}` is not a value of `{name}`"
        if close:
            msg += f"; did you mean {', '.join(f'`{c}`' for c in close)}?"
        else:
            shown = list(values)[:15]
            msg += f"; valid values include: {', '.join(shown)}"
        errors.append(msg)


def validate_query(query):
    """
    Validate a search template against the corpus inventory.

    Returns (is_valid, error_message).  error_message is a newline-joined
    list of all problems found (None when valid).  Structural correctness
    is largely left to Text-Fabric itself, which reports good line-based
    errors on execution; this validator focuses on what TF does NOT
    catch: nonexistent feature values and lexemes.
    """
    errors = []
    otypes = node_types()
    edges = edge_features()
    lines = query.split("\n")
    definedNames = set()
    sawAtom = False

    # First pass: collect defined names so relation lines can be checked.
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("%"):
            continue
        for tok in _tokenize(stripped):
            if ":" in tok and not tok.startswith((".", "-", "<")):
                name, _, rest = tok.partition(":")
                if re.fullmatch(r"[A-Za-z0-9_]+", name) and (
                    rest in otypes or rest == "." or rest == ""
                ):
                    definedNames.add(name)

    for lineNo, rawLine in enumerate(lines, 1):
        stripped = rawLine.strip()
        if not stripped or stripped.startswith("%"):
            continue
        if stripped in QUANT_KEYWORDS:
            if not sawAtom:
                errors.append(
                    f"line {lineNo}: quantifier `{stripped}` cannot appear "
                    f"before the atom it modifies"
                )
            continue
        tokens = _tokenize(stripped)

        # Relation line: `name op name`
        if len(tokens) == 3 and RELATION_OP.match(tokens[1]):
            for name in (tokens[0], tokens[2]):
                if name != ".." and name not in definedNames:
                    errors.append(
                        f"line {lineNo}: relation refers to `{name}` "
                        f"which is not a defined name"
                    )
            continue
        # Relation line with edge feature: `name -edge> name`
        if len(tokens) == 3 and EDGE_REL.match(tokens[1]):
            edgeName = EDGE_REL.match(tokens[1]).group(2)
            if edgeName not in edges:
                errors.append(
                    f"line {lineNo}: unknown edge feature `{edgeName}` "
                    f"(available: {', '.join(sorted(edges))})"
                )
            for name in (tokens[0], tokens[2]):
                if name != ".." and name not in definedNames:
                    errors.append(
                        f"line {lineNo}: relation refers to `{name}` "
                        f"which is not a defined name"
                    )
            continue

        # Atom line or feature continuation line.
        idx = 0
        # Optional leading relational operator on an atom line.
        if RELATION_OP.match(tokens[0]) or EDGE_REL.match(tokens[0]):
            idx = 1
            if len(tokens) == 1:
                errors.append(
                    f"line {lineNo}: operator `{tokens[0]}` needs an atom after it"
                )
                continue
        head = tokens[idx]
        headName, colon, headType = head.partition(":")
        isAtom = False
        if head == ".." :
            isAtom = True
        elif head in otypes or head == ".":
            isAtom = True
        elif colon and (headType in otypes or headType == "." or headType == ""):
            isAtom = True
        if isAtom:
            sawAtom = True
            featureTokens = tokens[idx + 1 :]
        else:
            # Not a recognizable atom head: either a continuation line of
            # feature specs, or a typo'd node type.
            first = FEATURE_SPEC.match(head)
            if (
                not sawAtom
                and first
                and first.group(2) is None
            ):
                close = _suggest(head, otypes | {"word", "phrase", "clause"})
                msg = f"line {lineNo}: `{head}` is not a node type"
                if close:
                    msg += f"; did you mean {', '.join(f'`{c}`' for c in close)}?"
                errors.append(msg)
                continue
            featureTokens = tokens[idx:]

        for tok in featureTokens:
            if EDGE_REL.match(tok):
                edgeName = EDGE_REL.match(tok).group(2)
                if edgeName not in edges:
                    errors.append(
                        f"line {lineNo}: unknown edge feature `{edgeName}`"
                    )
                continue
            _check_feature_spec(tok, lineNo, errors)

    if not any(
        line.strip() and not line.strip().startswith("%") for line in lines
    ):
        errors.append("query is empty")

    if errors:
        return False, "\n".join(errors)
    return True, None
