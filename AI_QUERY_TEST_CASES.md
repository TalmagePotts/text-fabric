# Complex AI Query Generation Test Cases

## Test Case 1: Advanced Quantifier with Lexeme Lookup

### Natural Language Prompt (what to send to AI):

```
Find all wayyiqtol narrative clauses in Genesis that contain the verb "say" (אמר) followed immediately by a quotation, but WITHOUT any preposition between the verb and the quotation marker. The clause must also have a subject phrase.
```

### Expected AI-Generated Query:

```
book book=Genesis
  clause kind=VC /with/
    phrase function=Subj
  /-/
  /where/
    w:word lex=>MR[ vt=wayq
  /have/
    w :> word lex=>MR
    /without/
      w << word sp=prep << word lex=>MR
    /-/
  /-/
```

### What This Tests:
- ✅ Lexeme lookup: "say" → `>MR[` (correct ETCBC transcription)
- ✅ Hebrew word recognition: אמר → `>MR[`
- ✅ Quantifiers: `/with/`, `/where/`+`/have/`, `/without/`
- ✅ Nested quantifiers (3 levels deep)
- ✅ Relational operators: `:>` (immediately after), `<<` (before)
- ✅ Feature combinations: `kind=VC`, `vt=wayq`, `sp=prep`
- ✅ Parent reference: `w` used across quantifier boundaries

---

## Test Case 2: Complex Construct Chain Analysis

### Natural Language Prompt:

```
Find construct chains where the first noun is feminine singular in construct state, followed immediately by a masculine singular noun in absolute state, and the phrase does NOT contain any adjectives. The phrase must be a nominal phrase.
```

### Expected AI-Generated Query:

```
phrase typ=NP /without/
  word sp=adjv
/-/
/where/
  n1:word sp=subs gn=f nu=sg st=c
  n2:word sp=subs gn=m nu=sg st=a
  n1 :> n2
/have/
  n1 < n2
/-/
```

### What This Tests:
- ✅ Quantifiers: `/without/`, `/where/`+`/have/`
- ✅ Multiple morphological features: `gn`, `nu`, `st`
- ✅ Adjacency operator: `:>` (immediately after)
- ✅ Canonical order: `<` (before)
- ✅ Named nodes: `n1`, `n2`
- ✅ Complex feature combinations

---

## Test Case 3: Rare Verbal Pattern with Negation

### Natural Language Prompt:

```
Find all hiphil perfect verbs in the book of Psalms that are NOT preceded by a negative particle (לא), but ARE followed by a prepositional phrase with the preposition "to" (ל). The verb must be third person.
```

### Expected AI-Generated Query:

```
book book=Psalmi
  clause
    v:word sp=verb vs=hif vt=perf ps=p3
    /without/
      neg:word lex=L>
      neg << v
    /-/
    pp:phrase typ=PP
    v < pp
    /where/
      word lex=L
    /have/
      .. sp=prep
    /-/
```

### What This Tests:
- ✅ Lexeme lookup: "not/no" → `L>` (negative particle)
- ✅ Lexeme lookup: "to" → `L` (preposition)
- ✅ Book name: "Psalms" → `Psalmi`
- ✅ Quantifiers: `/without/`, `/where/`+`/have/`
- ✅ Verbal morphology: `vs=hif`, `vt=perf`, `ps=p3`
- ✅ Parent reference: `..` in quantifier
- ✅ Multiple relational constraints

---

## Test Case 4: Discourse Analysis Pattern

### Natural Language Prompt:

```
Find nominal clauses in direct speech (quotations) where ALL words in the predicate phrase are either nouns or pronouns (no verbs), and the clause contains the divine name YHWH. The clause must NOT be followed by another clause within 3 words.
```

### Expected AI-Generated Query:

```
clause typ=NmCl domain=Q
  word lex=JHWH/
  /where/
    phrase function=Pred
    /where/
      word
    /have/
      /without/
        .. sp#subs|prps|nmpr
      /-/
    /-/
  /-/
  /without/
    c2:clause
    .. <3: c2
  /-/
```

### What This Tests:
- ✅ Lexeme lookup: "YHWH" → `JHWH/` (with suffix marker)
- ✅ Divine name recognition
- ✅ Clause types: `typ=NmCl`, `domain=Q`
- ✅ Triple-nested quantifiers
- ✅ Negation with alternatives: `sp#subs|prps|nmpr`
- ✅ Nearness operator: `<3:` (within 3 slots)
- ✅ Parent reference: `..` at multiple levels

---

## Test Case 5: Syntactic Rarity Search

### Natural Language Prompt:

```
Find clauses where the verb "give" (נתן) appears in qal stem, and there are exactly two object phrases - one direct object and one indirect object with the preposition "to" (ל) - but the clause does NOT contain any conjunction words.
```

### Expected AI-Generated Query:

```
clause /without/
  word sp=conj
/-/
/where/
  word lex=NTN[ vs=qal
/have/
  /with/
    phrase function=Objc
    /without/
      word lex=L
    /-/
  /or/
    phrase function=Cmpl
  /-/
  /with/
    phrase function=Objc
    /where/
      word lex=L
    /have/
      .. sp=prep
    /-/
  /or/
    phrase function=Cmpl
    /where/
      word lex=L
    /have/
      .. sp=prep
    /-/
  /-/
/-/
```

### What This Tests:
- ✅ Lexeme lookup: "give" → `NTN[`
- ✅ Lexeme lookup: "to" → `L`
- ✅ Complex quantifier nesting (4+ levels)
- ✅ Multiple `/with/`+`/or/` alternatives
- ✅ Phrase functions: `Objc`, `Cmpl`
- ✅ Negation: `/without/`
- ✅ Parent reference in nested contexts

---

## Test Case 6: Ultra-Complex Research Query

### Natural Language Prompt:

```
In the book of Isaiah, find wayyiqtol clauses where the verb "come" (בוא) is in qal stem, the clause has a subject that is a proper noun (name), and there is a time phrase, but the clause does NOT contain the word "day" (יום) anywhere, and is NOT immediately followed by another wayyiqtol clause.
```

### Expected AI-Generated Query:

```
book book=Jesaia
  c1:clause typ=WayX
    word lex=BW> vs=qal vt=wayq
    phrase function=Subj
    /where/
      word sp=nmpr
    /have/
      .. sp=nmpr
    /-/
    phrase function=Time
    /without/
      word lex=JWM
    /-/
    /without/
      c2:clause typ=WayX
      c1 :> c2
    /-/
```

### What This Tests:
- ✅ Lexeme lookup: "come" → `BW>` (bet-vav-aleph)
- ✅ Lexeme lookup: "day" → `JWM` (yod-vav-mem)
- ✅ Book name: "Isaiah" → `Jesaia`
- ✅ Clause type: `typ=WayX` (wayyiqtol clause)
- ✅ Multiple quantifiers on same atom
- ✅ Nested `/where/`+`/have/` with parent reference
- ✅ Multiple `/without/` quantifiers
- ✅ Adjacency check: `:>` between clauses
- ✅ Named nodes for clause comparison

---

## How to Test

### For Each Test Case:

1. **Copy the "Natural Language Prompt"** into the AI query generator
2. **Verify the AI generates** a query matching the expected structure
3. **Check for:**
   - ✅ Correct lexeme spellings (case-sensitive ETCBC)
   - ✅ Proper quantifier syntax (indentation, `/-/` terminators)
   - ✅ Correct feature names (`sp`, `lex`, `vs`, `vt`, etc.)
   - ✅ Valid relational operators
   - ✅ Parent references (`..`) where appropriate

### Success Criteria:

- **Syntax**: Query is valid Text-Fabric syntax
- **Lexemes**: All lexemes match ETCBC transcription exactly
- **Features**: All feature names are correct
- **Logic**: Query captures the intended research question
- **Quantifiers**: Proper nesting and termination

### Expected Challenges:

These queries test the AI's ability to:
- Handle complex nested quantifiers (3-4 levels deep)
- Look up Hebrew lexemes correctly
- Use parent references (`..`) appropriately
- Combine multiple quantifier types
- Apply proper indentation across nesting levels
- Use correct relational operators for different contexts

---

## Recommended Testing Order:

1. **Test Case 3** (easiest) - Single quantifier, basic lexemes
2. **Test Case 2** (medium) - Construct chains, morphology
3. **Test Case 1** (hard) - Multiple quantifiers, complex nesting
4. **Test Case 5** (very hard) - Multiple alternatives, deep nesting
5. **Test Case 4** (expert) - Triple nesting, discourse features
6. **Test Case 6** (ultimate) - Everything combined

Good luck! These queries will thoroughly test the production template's capabilities.
