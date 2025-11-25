# Text-Fabric Quantifier Patterns Guide

## Overview

Quantifiers are powerful expressions in Text-Fabric search templates that assert conditions on atoms. They allow you to express complex logical constraints like "find clauses WITHOUT verbs" or "find phrases where ALL words are masculine."

## The Three Quantifier Types

### 1. `/without/` - Exclusion

**Purpose:** Find nodes that do NOT contain a specific pattern

**Syntax:**
```
atom /without/
  template
/-/
```

**Semantics:** Returns nodes matching `atom` for which there is NO match of `template`

**Parent Reference:** Use `..` to refer to the quantified atom within the template

---

#### Example 1: Clauses Without Verbs

**Query:**
```
clause /without/
  word sp=verb
/-/
```

**Meaning:** Find all clauses that do not contain any verb

**Use Case:** Finding nominal clauses, elliptical clauses

---

#### Example 2: Feminine Words That Are NOT Plural

**Query:**
```
word gn=f /without/
  .. nu=pl
/-/
```

**Meaning:** Find feminine words that are not plural (i.e., singular or dual)

**Note:** The `..` refers back to the word being quantified

---

#### Example 3: Clauses Without Following Preposition

**Query:**
```
c:clause /without/
  p:word sp=prep
  c << p
/-/
```

**Meaning:** Find clauses that are not followed by a preposition

**Use Case:** Identifying clause boundaries, finding independent clauses

---

#### Example 4: Nominal Clauses Without Copula

**Query:**
```
clause typ=NmCl /without/
  word lex=HJH
/-/
```

**Meaning:** Find nominal clauses that don't contain the verb "to be" (HJH)

**Use Case:** Identifying verbless nominal clauses

---

#### Example 5: Phrases Without Articles

**Query:**
```
phrase /without/
  word sp=art
/-/
```

**Meaning:** Find phrases that don't contain the article

**Use Case:** Finding indefinite phrases

---

### 2. `/where/` + `/have/` - Universal Quantification

**Purpose:** Assert that ALL instances of a pattern satisfy a condition

**Syntax:**
```
atom /where/
  templateA
/have/
  templateH
/-/
```

**Semantics:** For ALL tuples matching `(atom, templateA)`, there must exist a match for `(atom, templateA, templateH)`

**In other words:** "For all A, there exists H"

---

#### Example 6: Clauses Where All Predicate Phrases Contain Verbs

**Query:**
```
clause /where/
  phrase function=Pred
/have/
  word sp=verb
/-/
```

**Meaning:** Find clauses where every predicate phrase contains at least one verb

**Use Case:** Ensuring verbal predication

---

#### Example 7: Phrases Where All Words Are Masculine

**Query:**
```
phrase /where/
  word
/have/
  .. gn=m
/-/
```

**Meaning:** Find phrases where every word is masculine

**Use Case:** Gender agreement analysis

---

#### Example 8: Clauses Where All Verbs Are Qal

**Query:**
```
clause /where/
  word sp=verb
/have/
  .. vs=qal
/-/
```

**Meaning:** Find clauses where all verbs (if any) are in the qal stem

**Note:** This will also match clauses with no verbs (vacuous truth)

---

#### Example 9: Sentences Where All Clauses Are Verbal

**Query:**
```
sentence /where/
  clause
/have/
  .. kind=VC
/-/
```

**Meaning:** Find sentences where every clause is a verbal clause

**Use Case:** Identifying action-heavy narrative

---

#### Example 10: Nested Quantifier - Predicate Phrases With Only Verbs

**Query:**
```
phrase function=Pred /where/
  word
/have/
/without/
  .. sp#verb
/-/
/-/
```

**Meaning:** Find predicate phrases where all words are verbs (no non-verbs)

**Breakdown:**
- Outer quantifier: For all words in the phrase...
- Inner quantifier: ...there should NOT exist a word that is not a verb
- Equivalent to: "All words are verbs"

---

### 3. `/with/` + `/or/` - Existential Quantification

**Purpose:** Assert that AT LEAST ONE of several patterns matches

**Syntax:**
```
atom /with/
  template1
/or/
  template2
/or/
  template3
/-/
```

**Semantics:** There exists a match for at least one of the templates

**Note:** Can have any number of `/or/` alternatives (including zero)

---

#### Example 11: Clauses With Subject OR Object Phrase

**Query:**
```
clause /with/
  phrase function=Subj
/or/
  phrase function=Objc
/-/
```

**Meaning:** Find clauses that have either a subject phrase or an object phrase (or both)

**Use Case:** Finding clauses with explicit arguments

---

#### Example 12: Words That Are Verbs OR Nouns

**Query:**
```
word /with/
  .. sp=verb
/or/
  .. sp=subs
/-/
```

**Meaning:** Find words that are either verbs or nouns

**Note:** This is equivalent to `word sp=verb|subs` but demonstrates quantifier usage

---

#### Example 13: Clauses With Wayyiqtol OR Perfect Verbs

**Query:**
```
clause /with/
  word vt=wayq
/or/
  word vt=perf
/-/
```

**Meaning:** Find clauses containing either wayyiqtol or perfect verbs

**Use Case:** Narrative vs. discourse analysis

---

#### Example 14: Phrases With Preposition OR Conjunction

**Query:**
```
phrase /with/
  word sp=prep
/or/
  word sp=conj
/-/
```

**Meaning:** Find phrases containing either a preposition or a conjunction

---

#### Example 15: Single Alternative (Equivalent to Containment)

**Query:**
```
clause /with/
  word sp=verb
/-/
```

**Meaning:** Find clauses containing a verb

**Note:** This is similar to:
```
clause
  word sp=verb
```

**Difference:** The first returns tuples with only the clause; the second returns tuples with (clause, word)

---

## Quantifier Rules & Restrictions

### Indentation Rules

**Critical:** Quantifier keywords must have the SAME indentation as the atom they quantify

**Correct:**
```
clause /without/
  word sp=verb
/-/
```

**Wrong:**
```
clause
  /without/
  word sp=verb
/-/
```

**Templates inside quantifiers must be indented MORE than the keywords:**

**Correct:**
```
clause /without/
  word sp=verb
/-/
```

**Wrong:**
```
clause /without/
word sp=verb
/-/
```

### Parent Reference

**Use `..` to refer to the quantified atom:**

```
word gn=f /without/
  .. nu=pl
/-/
```

The `..` refers to the word with `gn=f`

**You can also use the atom's name if it has one:**

```
w:word gn=f /without/
  w nu=pl
/-/
```

### Name Visibility & Scoping

**Names defined in outer quantifiers are NOT accessible in inner quantifiers:**

```
clause /where/
  p:phrase function=Pred
/have/
  word sp=verb
  % Cannot reference 'p' here - it's in outer quantifier
/-/
```

**Names defined in inner quantifiers are NOT accessible in outer quantifiers:**

```
clause /where/
  phrase function=Pred
  /without/
    v:word sp=verb
  /-/
/have/
  % Cannot reference 'v' here - it's in inner quantifier
/-/
```

**In `/with/`, alternatives cannot share names:**

```
clause /with/
  p:phrase function=Subj
/or/
  % Cannot reference 'p' from first alternative
  phrase function=Objc
/-/
```

**In `/where/`, templateH can use names from templateA (if defined outside any quantifier):**

```
clause /where/
  p:phrase function=Pred
/have/
  p [[ word sp=verb
/-/
```

The `p` is accessible in the `/have/` section because it's defined in the `/where/` section (not inside a nested quantifier).

### Nesting Quantifiers

**Quantifiers can be nested to express complex logic:**

**Example: Clauses where all predicate phrases have only verbs**

```
clause /where/
  phrase function=Pred
/have/
/without/
  word sp#verb
/-/
/-/
```

**Breakdown:**
1. Outer `/where/` `/have/`: For all predicate phrases...
2. Inner `/without/`: ...there should not exist...
3. ...a word that is not a verb

**Think about expansion:** When nested, quantifiers are expanded into separate search templates. The inner quantifier becomes:

```
phrase function=Pred
  word sp#verb
```

And the outer quantifier checks that this returns no results for each predicate phrase.

### Relative Indentation Preservation

**When quantifiers are expanded, relative indentation is preserved:**

**Original:**
```
clause /where/
  phrase function=Pred
  /have/
    word sp=verb
  /-/
/-/
```

**Expanded auxiliary template:**
```
clause
  phrase function=Pred
    word sp=verb
```

The relative indentation (phrase indented under clause, word under phrase) is maintained.

---

## Common Patterns & Use Cases

### Pattern 1: Exclusion with Relational Constraint

**Find clauses not followed by another clause:**

```
c1:clause /without/
  c2:clause
  c1 << c2
/-/
```

### Pattern 2: Universal Property

**Find phrases where all words have the same gender:**

```
phrase /where/
  w1:word
  w2:word
  w1 # w2
/have/
  w1 .gn. w2
/-/
```

### Pattern 3: Existential with Multiple Alternatives

**Find clauses with any type of complement:**

```
clause /with/
  phrase function=Cmpl
/or/
  phrase function=Objc
/or/
  phrase function=Loca
/-/
```

### Pattern 4: Nested Exclusion

**Find clauses without any non-verbal words:**

```
clause /without/
  word sp#verb
/-/
```

This is simpler than:

```
clause /where/
  word
/have/
  .. sp=verb
/-/
```

But they mean different things:
- First: No non-verbal words (could have zero words)
- Second: All words are verbal (requires at least one word)

---

## Debugging Quantifier Queries

### Common Errors

**Error 1: Missing `/-/` terminator**

```
clause /without/
  word sp=verb
```

**Fix:** Add `/-/`:

```
clause /without/
  word sp=verb
/-/
```

**Error 2: Wrong indentation of `/-/`**

```
clause /without/
  word sp=verb
  /-/
```

**Fix:** Align `/-/` with quantifier keyword:

```
clause /without/
  word sp=verb
/-/
```

**Error 3: Referencing names across quantifier boundaries**

```
clause /where/
  p:phrase
/have/
/with/
  p [[ word
/-/
/-/
```

**Fix:** Don't reference outer names in inner quantifiers. Restructure:

```
clause /where/
  phrase
/have/
/with/
  .. [[ word
/-/
/-/
```

**Error 4: Confusing `/with/` with simple containment**

```
% This returns (clause,) tuples
clause /with/
  word sp=verb
/-/

% This returns (clause, word) tuples
clause
  word sp=verb
```

Choose based on what you want in the result tuples.

---

## Advanced Examples

### Example 16: Clauses With Both Subject and Predicate

```
clause /with/
  phrase function=Subj
/-/
/with/
  phrase function=Pred
/-/
```

**Note:** Multiple quantifiers on the same atom

### Example 17: Verses Without Divine Name

```
verse /without/
  word lex=JHWH/
/-/
```

### Example 18: Sentences Where No Clause Has a Verb

```
sentence /where/
  clause
/have/
/without/
  word sp=verb
/-/
/-/
```

### Example 19: Phrases With All Words in Construct State

```
phrase /where/
  word sp=subs
/have/
  .. st=c
/-/
```

### Example 20: Complex Nested Logic

**Find clauses where all phrases are either prepositional or contain only one word:**

```
clause /where/
  phrase
/have/
/with/
  .. typ=PP
/or/
/without/
  w1:word
  w2:word
  w1 # w2
/-/
/-/
/-/
```

**Breakdown:**
- For all phrases in the clause...
- ...either the phrase is a PP...
- ...or there don't exist two different words in it (i.e., it has at most one word)

---

## Summary

| Quantifier | Logic | Use When |
|------------|-------|----------|
| `/without/` | NOT EXISTS | Excluding patterns |
| `/where/` `/have/` | FOR ALL ... EXISTS | Universal properties |
| `/with/` `/or/` | EXISTS (one of) | Alternative patterns |

**Key Principles:**
1. Use `..` to reference the parent atom
2. Maintain proper indentation (keywords align with atom, templates indent further)
3. Always terminate with `/-/`
4. Understand name scoping (no cross-boundary references)
5. Think about quantifier expansion into auxiliary templates
