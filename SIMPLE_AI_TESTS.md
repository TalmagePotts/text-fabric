# CORRECTED Simple Test Case for AI Query Generation

Based on user feedback, here's a VERIFIED working test case:

## ✅ SIMPLE TEST - Start Here

### What to Send to AI:

```
Find all hiphil perfect verbs in Psalms that are third person
```

### What AI Should Return:

```
book book=Psalmi
  word sp=verb vs=hif vt=perf ps=p3
```

### Verification:
- ✅ Book name: "Psalms" → `Psalmi` (Latin)
- ✅ Features: `sp=verb`, `vs=hif`, `vt=perf`, `ps=p3`
- ✅ Simple containment (no quantifiers)

---

## ✅ MEDIUM TEST - With Quantifier

### What to Send to AI:

```
Find clauses in Genesis that do NOT contain any verbs
```

### What AI Should Return:

```
book book=Genesis
  clause /without/
    word sp=verb
  /-/
```

### Verification:
- ✅ Book name: `Genesis` (same in Latin)
- ✅ Quantifier: `/without/` with proper indentation
- ✅ Terminator: `/-/` aligned with `/without/`
- ✅ Containment: word inside quantifier, quantifier inside clause

---

## ✅ ADVANCED TEST - Multiple Features + Lexeme

### What to Send to AI:

```
Find the verb "give" in qal stem, perfect tense, third person masculine singular
```

### What AI Should Return:

```
word lex=NTN[ sp=verb vs=qal vt=perf ps=p3 gn=m nu=sg
```

### Verification:
- ✅ Lexeme: "give" → `NTN[` (with `[` doubling marker)
- ✅ All features on one line (simple query)
- ✅ Morphology: `vs=qal`, `vt=perf`, `ps=p3`, `gn=m`, `nu=sg`

---

## ⚠️ KNOWN ISSUES FROM USER TESTING

### Issue 1: Lexeme Markers
**Problem:** AI adds markers incorrectly

**Examples:**
- ❌ `word lex=JWM/` - WRONG! `JWM` has NO `/` marker
- ❌ `word lex=BW>[` - WRONG! `BW>` has NO `[` marker
- ✅ `word lex=JHWH/` - CORRECT! This one HAS `/`
- ✅ `word lex=NTN[` - CORRECT! This one HAS `[`

**Fix:** Added to production template:
```markdown
**CRITICAL:** Not all lexemes have `[` or `/` markers! Check database!
```

### Issue 2: Book Names
**Problem:** AI uses English names instead of Latin

**Examples:**
- ❌ `book book=Isaiah` - WRONG!
- ✅ `book book=Jesaia` - CORRECT!
- ❌ `book book=Psalms` - WRONG!
- ✅ `book book=Psalmi` - CORRECT!

**Fix:** Added complete book name list to production template

### Issue 3: Quantifier Placement
**Problem:** AI puts quantifiers outside containment hierarchy

**Wrong:**
```
book book=Jesaia
  c1:clause typ=WayX
  /without/
    word lex=JWM
  /-/
    word lex=BW>
```

**Correct:**
```
book book=Jesaia
  c1:clause typ=WayX
    word lex=BW>
    /without/
      word lex=JWM
    /-/
```

**Key:** Quantifiers must be INSIDE the atom they quantify, maintaining indentation

---

## 📋 Testing Checklist

When testing AI-generated queries, check:

1. **Lexeme Accuracy:**
   - [ ] Correct ETCBC transcription (case-sensitive)
   - [ ] Markers (`[`, `/`) only when needed
   - [ ] No English words (should be transliterated)

2. **Book Names:**
   - [ ] Latin forms used (Jesaia, Psalmi, Proverbia, etc.)
   - [ ] NOT English (Isaiah, Psalms, Proverbs)

3. **Feature Names:**
   - [ ] `sp` not `pos`
   - [ ] `gn` not `gender`
   - [ ] `nu` not `number`
   - [ ] `vs` not `stem`
   - [ ] `vt` not `tense`

4. **Quantifier Syntax:**
   - [ ] Keywords (`/without/`, `/where/`, `/have/`, `/with/`, `/or/`) at correct indentation
   - [ ] Templates indented MORE than keywords
   - [ ] Terminators (`/-/`) aligned with opening keyword
   - [ ] Quantifiers INSIDE the atom they quantify

5. **Indentation:**
   - [ ] 2 spaces per level
   - [ ] No tabs
   - [ ] Consistent throughout
   - [ ] Maintains containment hierarchy

---

## 🎯 Recommended Testing Order

1. **Simple query** (no quantifiers, no lexemes)
2. **Lexeme query** (test lexeme lookup)
3. **Book-specific query** (test book names)
4. **Single quantifier** (test `/without/`)
5. **Complex query** (combine everything)

Start simple and build up complexity!
