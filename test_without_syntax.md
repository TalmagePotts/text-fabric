# Text-Fabric `/without/` Quantifier - Correct Syntax

Based on analysis of working queries in the codebase, here's the **correct syntax**:

## Key Rule: Indentation Matters!

The `/without/` keyword must be at **0 indentation** (no spaces) when it quantifies a top-level atom.

## Working Examples from Codebase

### Example 1: Simple exclusion (verseOrdinary.txt)
```
verse
/without/
  word freq_lex<70
/-/
```

### Example 2: Tablet without case (tabletWithoutCase.txt)
```
tablet
/without/
  case
/-/
```

### Example 3: Clause without subject-predicate pattern (stephenVerblessClauses2.txt)
```
c:clause
/without/
  phrase function=Subj
  << phrase function=Pred
/-/
  p:phrase function=Subj
    phrase_atom rela#Appo|Para|Spec
      word pdp=subs|nmpr|prps|prde|prin|adjv
  << phrase function=PreC
  /without/
    word pdp=prep
  /-/
    word pdp=subs|nmpr|prin|adjv ls=card|ordn
```

## Pattern for Your Queries

### Query 1: Nominal clause without preposition after noun

**CORRECT:**
```
clause typ=NmCl
  n:word sp=subs
/without/
  p:word sp=prep
  n :> p
/-/
```

### Query 2: Verb without noun after it

**CORRECT:**
```
word sp=verb
/without/
  :> word sp=subs
/-/
```

## Critical Rules

1. **Top-level `/without/`** = 0 spaces indentation
2. **Nested `/without/`** = same indentation as the atom it quantifies
3. **Content inside `/without/`** = indented 2 more spaces than `/without/`
4. **`/-/`** = same indentation as `/without/`
5. **Content after `/-/`** = continues at the parent atom's level

## The Error You Got

Your error "Does not immediately follow an atom at the same level" means the `/without/` was indented when it should have been at column 0 (for top-level atoms).

