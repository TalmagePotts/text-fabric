# AI Query Generation — Test Cases

> **Note:** The authoritative, executable test suite lives in
> `test/browser/test_query_validator.py` (runs anywhere) and
> `test/browser/test_ai_pipeline.py` (runs against the live corpus;
> the end-to-end class needs `GEMINI_API_KEY` or `ANTHROPIC_API_KEY`).
> This file documents the two showcase cases in human-readable form.
> Every query below has been executed against the live BHSA corpus —
> result counts included. (The previous version of this file contained
> "expected" queries that did not actually parse; they taught the AI
> wrong quantifier placement and have been replaced.)

## Test Case 1: Wayyiqtol of אמר in Genesis, clause has a subject

### Natural language prompt

```
Find wayyiqtol forms of the verb "say" (אמר) in Genesis, in verbal
clauses that have an explicit subject phrase.
```

### Verified query (186 results)

```
book book=Genesis
  clause kind=VC
  /with/
    phrase function=Subj
  /-/
    w:word lex=>MR[ vt=wayq
```

What this tests: lexeme lookup ("say"/אמר → `>MR[`), quantifier
placement (keywords at the same indentation as the `clause` atom,
immediately after it), children resuming after `/-/`.

## Test Case 2: Construct chain in an adjective-free NP

### Natural language prompt

```
Find construct chains where a feminine singular noun in construct state
is immediately followed by a masculine singular noun in absolute state,
inside a nominal phrase that contains no adjectives.
```

### Verified query (395 results)

```
phrase typ=NP
/without/
  word sp=adjv
/-/
  n1:word sp=subs gn=f nu=sg st=c
  n2:word sp=subs gn=m nu=sg st=a
  n1 <: n2
```

What this tests: `/without/` quantifier, named atoms, the adjacency
operator `<:` (n1 ends immediately before n2 starts), morphological
feature combinations.

## Quantifier placement rules (the thing the old file got wrong)

- Quantifier keywords (`/without/`, `/where/`, `/have/`, `/with/`,
  `/or/`, `/-/`) sit at **exactly the same indentation** as the atom
  they modify, on the lines **immediately following** it.
- The sub-template inside is indented deeper.
- Every quantifier is terminated by `/-/`.
- Atoms inside quantifiers do **not** appear in result rows.
- Names defined outside a quantifier are **not** visible inside it
  (only `..` and the quantified atom's own name are).
