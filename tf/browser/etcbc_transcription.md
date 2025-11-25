# ETCBC Hebrew Transcription Reference

## Overview

The ETCBC (Eep Talstra Centre for Bible and Computer) transcription system is an ASCII-based encoding for Biblical Hebrew. It is used throughout the BHSA Text-Fabric dataset for representing Hebrew consonants, vowels, and diacritical marks.

**Key Characteristics:**
- **ASCII-only:** All characters are standard ASCII (no Unicode required for base transcription)
- **Case-sensitive:** Uppercase and lowercase have different meanings
- **Unambiguous:** One-to-one mapping between Hebrew and transcription

---

## Consonants

### Basic Consonants

| Hebrew | Unicode | ETCBC | Name | Notes |
|--------|---------|-------|------|-------|
| א | U+05D0 | `>` | aleph | Glottal stop |
| ב | U+05D1 | `B` | bet | /b/ or /v/ |
| ג | U+05D2 | `G` | gimel | /g/ |
| ד | U+05D3 | `D` | dalet | /d/ |
| ה | U+05D4 | `H` | he | /h/ |
| ו | U+05D5 | `W` | vav | /w/ or /v/ |
| ז | U+05D6 | `Z` | zayin | /z/ |
| ח | U+05D7 | `X` | het | /ħ/ (voiceless pharyngeal) |
| ט | U+05D8 | `V` | tet | /t/ (emphatic) |
| י | U+05D9 | `J` | yod | /j/ (English 'y') |
| כ | U+05DB | `K` | kaf | /k/ |
| ל | U+05DC | `L` | lamed | /l/ |
| מ | U+05DE | `M` | mem | /m/ |
| נ | U+05DF | `N` | nun | /n/ |
| ס | U+05E1 | `S` | samekh | /s/ |
| ע | U+05E2 | `<` | ayin | /ʕ/ (voiced pharyngeal) |
| פ | U+05E4 | `P` | pe | /p/ or /f/ |
| צ | U+05E6 | `Y` | tsade | /ts/ |
| ק | U+05E7 | `Q` | qof | /q/ (uvular) |
| ר | U+05E8 | `R` | resh | /r/ |
| שׂ | U+05E9+U+05C2 | `&` | sin | /s/ (left dot) |
| שׁ | U+05E9+U+05C1 | `C` | shin | /ʃ/ (right dot) |
| ת | U+05EA | `T` | tav | /t/ |

### Final Forms

Hebrew has five letters with special final forms (used at end of word). In ETCBC transcription, these use the same letter as the regular form:

| Hebrew Final | Regular | ETCBC | Name |
|--------------|---------|-------|------|
| ך | כ | `K` | kaf sofit |
| ם | מ | `M` | mem sofit |
| ן | נ | `N` | nun sofit |
| ף | פ | `P` | pe sofit |
| ץ | צ | `Y` | tsade sofit |

### Dagesh (Doubling/Hardening)

**Dagesh Forte** (doubling): Indicated by `.` after the letter
- Example: `B.` = ב with dagesh forte (doubled /bb/)

**Dagesh Lene** (hardening for בגדכפת): Also indicated by `.`
- Applies to: B, G, D, K, P, T
- Example: `B.` = ב with dagesh lene (/b/ not /v/)

**Mappiq** (in ה): Indicated by `.`
- Example: `H.` = ה with mappiq (pronounced /h/)

### Special Markers

| Symbol | Meaning | Example |
|--------|---------|---------|
| `[` | Gemination/doubling marker | `NTN[` (give) |
| `/` | Suffix/ending marker | `JHWH/` (YHWH) |
| `.` | Dagesh forte/lene/mappiq | `B.`, `K.` |

---

## Common Lexeme Examples

### Most Frequent Lexemes

| ETCBC | Hebrew | Gloss | Frequency | Notes |
|-------|--------|-------|-----------|-------|
| `L` | ל | to, for | 20,069 | Preposition |
| `B` | ב | in, with | ~15,000 | Preposition |
| `W` | ו | and | ~50,000 | Conjunction (as prefix) |
| `H` | ה | the | ~24,000 | Article (as prefix) |
| `MN` | מן | from | ~7,000 | Preposition |
| `<L` | על | on, upon | ~5,700 | Preposition |
| `>T` | את | (object marker) | ~10,000 | Particle |
| `JHWH/` | יהוה | YHWH | 6,828 | Divine name |
| `>LHM` | אלהים | God/gods | ~2,600 | Noun |
| `>MR[` | אמר | say | ~5,300 | Verb |
| `HJH` | היה | be | ~3,500 | Verb |
| `NTN[` | נתן | give | ~2,000 | Verb |
| `BR>[` | ברא | create | ~50 | Verb |
| `MLK` | מלך | king | ~2,500 | Noun |
| `BN` | בן | son | ~4,900 | Noun |
| `>RY` | ארץ | earth, land | ~2,500 | Noun |
| `JWM` | יום | day | ~2,300 | Noun |

### Lexeme Patterns

**Verbs often end with `[`:**
- `>MR[` - say
- `NTN[` - give
- `BR>[` - create
- `HLK[` - walk, go
- `JC>[` - go out

**Divine names often end with `/`:**
- `JHWH/` - YHWH
- `>LHJM/` - Elohim (variant)

**Prepositions are usually short:**
- `L` - to, for
- `B` - in
- `MN` - from
- `<L` - on
- `>L` - to, toward
- `K` - like, as

---

## Vowels (Pointed Transcription)

For pointed (vocalized) forms, ETCBC uses additional characters:

### Vowel Points

| Hebrew | ETCBC | Name | Sound |
|--------|-------|------|-------|
| ַ (patah) | `A` | patah | /a/ |
| ָ (qamets) | `:A` | qamets | /a/ or /o/ |
| ֶ (segol) | `E` | segol | /e/ |
| ֵ (tsere) | `:E` | tsere | /e/ |
| ִ (hiriq) | `I` | hiriq | /i/ |
| ָ (holam) | `O` | holam | /o/ |
| ֻ (qubuts) | `U` | qubuts | /u/ |
| ְ (sheva) | `:` | sheva | /ə/ or silent |
| ֲ (hataf patah) | `A@` | hataf patah | /a/ (reduced) |
| ֱ (hataf segol) | `E@` | hataf segol | /e/ (reduced) |
| ֳ (hataf qamets) | `O@` | hataf qamets | /o/ (reduced) |

### Vowel Letter Indicators

| Hebrew | ETCBC | Name |
|--------|-------|------|
| ָי (hiriq yod) | `IJ` | hiriq male |
| ֵי (tsere yod) | `:EJ` | tsere male |
| וֹ (holam vav) | `OW` | holam male |
| וּ (shuruq) | `W.` | shuruq |

---

## Other Diacritical Marks

### Dagesh and Mappiq

| Mark | ETCBC | Usage |
|------|-------|-------|
| Dagesh forte | `.` | Doubling: `B.` |
| Dagesh lene | `.` | Hardening: `K.` |
| Mappiq | `.` | In ה: `H.` |

### Maqqef and Sof Pasuq

| Mark | ETCBC | Name | Meaning |
|------|-------|------|---------|
| ־ (maqqef) | `-` | maqqef | Word joiner (hyphen) |
| ׃ (sof pasuq) | `00` | sof pasuq | Verse end marker |

---

## Accents (Cantillation Marks)

ETCBC includes full encoding for all cantillation marks (te'amim). These are complex and used for chanting/reading the text. Common ones:

| Hebrew | ETCBC | Name |
|--------|-------|------|
| ֑ | `01` | etnahta |
| ֽ | `05` | merkha |
| ֥ | `65` | munah |
| ֖ | `74` | tifha |
| ֗ | `85` | revia |

**Note:** For lexeme queries, accents are typically not included in the `lex` feature (consonantal only).

---

## Transcription Rules for Queries

### When Searching by Lexeme (`lex` feature)

**Use consonantal transcription only:**
- ✅ `word lex=JHWH/`
- ✅ `word lex=NTN[`
- ✅ `word lex=>MR[`
- ❌ `word lex=YHWH` (wrong: use J not Y, missing /)
- ❌ `word lex=natan` (wrong: use ETCBC, not transliteration)

**Case sensitivity:**
- ✅ `word lex=BR>[` (correct)
- ❌ `word lex=br>[` (wrong: lowercase)

**Special characters:**
- ✅ `word lex=>LHM` (aleph = >)
- ✅ `word lex=<BR` (ayin = <)
- ✅ `word lex=NTN[` (doubling = [)
- ✅ `word lex=JHWH/` (suffix = /)

### When Searching by Pointed Forms

**For `g_lex` (pointed lexeme):**
- Use vowel markers: `:`, `;`, `@`
- Example: `word g_lex=R;>CIJ` (beginning)

**For `g_word` (pointed word):**
- Full vocalization with accents
- Example: `word g_word=B:;R;>CIJT` (in beginning)

### When Searching by Unicode

**For `lex_utf8`, `g_word_utf8`, etc.:**
- Use actual Hebrew Unicode characters
- Example: `word lex_utf8~^אמר` (words starting with אמר)
- Regex is useful: `word g_word_utf8~^בְּ` (words starting with ב + sheva)

---

## Quick Reference: ETCBC Special Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `>` | Aleph (א) | `>MR[` (say) |
| `<` | Ayin (ע) | `<BR` (pass over) |
| `[` | Doubling/gemination | `NTN[` (give) |
| `/` | Suffix marker | `JHWH/` (YHWH) |
| `.` | Dagesh/mappiq | `B.` (bet with dagesh) |
| `:` | Sheva or long vowel | `:A` (qamets) |
| `;` | Vowel marker | `R;>C` |
| `@` | Reduced vowel | `A@` (hataf patah) |
| `&` | Sin (שׂ) | `&M` |
| `X` | Het (ח) | `XWY` (live) |
| `V` | Tet (ט) | `VWB` (good) |
| `Y` | Tsade (צ) | `YDQ` (righteous) |
| `C` | Shin (שׁ) | `CWB` (return) |
| `J` | Yod (י) | `JWM` (day) |
| `W` | Vav (ו) | `WJH` (and it was) |

---

## Common Mistakes & Corrections

| ❌ Wrong | ✅ Correct | Issue |
|---------|-----------|-------|
| `YHWH` | `JHWH/` | Use J for yod, add / |
| `amar` | `>MR[` | Use ETCBC, not transliteration |
| `give` | `NTN[` | Use Hebrew, not English |
| `br>` | `BR>[` | Uppercase, add [ |
| `elohim` | `>LHM` | Use ETCBC consonants |
| `shalom` | `CLWM` | Use C for shin |
| `torah` | `TWRH` | Use W for vav |

---

## Lookup Strategy for AI

When a user mentions a Hebrew word:

1. **Check if it's a common word** (see table above)
2. **Search lexeme database** by:
   - ETCBC transcription (if user provides it)
   - English gloss (if user provides English)
   - Hebrew Unicode (if user provides Hebrew)
3. **Verify exact spelling** before using in query
4. **Use consonantal form** for `lex` feature
5. **Use pointed form** for `g_lex` feature (if needed)

**Example workflow:**
- User says: "Find the word 'give'"
- AI searches lexeme database for gloss containing "give"
- Finds: `NTN[` with gloss "give"
- Generates query: `word lex=NTN[`

---

## Summary

**For Text-Fabric queries:**
- Use **consonantal ETCBC transcription** for `lex` feature
- **Case-sensitive** (uppercase for consonants)
- **Special characters**: `>` (aleph), `<` (ayin), `[` (doubling), `/` (suffix)
- **Always verify** lexeme spelling from database
- **Never guess** - look up the exact form

**Key principle:** The ETCBC transcription is the authoritative form in the BHSA dataset. When in doubt, consult the lexeme database.
