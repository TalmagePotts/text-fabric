# Hebrew Text Normalizer

A robust Python module for normalizing Hebrew text to enable matching between different Hebrew text sources (Strong's Concordance and BHSA).

## Features

- **Niqqud Removal**: Strip all vowel points (niqqud) and diacritical marks
- **Final Form Normalization**: Convert final letter forms to regular forms (ך→כ, ם→מ, ן→נ, ף→פ, ץ→צ)
- **Fuzzy Matching**: Compare Hebrew texts with Levenshtein distance
- **Spelling Variant Detection**: Handle plene vs. defective spelling
- **Data Source Integration**: Extract and normalize from Strong's and BHSA formats

## Installation

No external dependencies required! Uses only Python standard library.

```bash
# Just copy the file to your project
cp hebrew_normalizer.py /path/to/your/project/
```

## Quick Start

```python
from hebrew_normalizer import normalize_hebrew, compare_hebrew

# Normalize Hebrew text (remove niqqud, normalize final forms)
text = 'אָהַב'  # "love" with vowel points
normalized = normalize_hebrew(text)
print(normalized)  # Output: 'אהב'

# Compare two Hebrew texts
score = compare_hebrew('אָהַב', 'אהב')
print(score)  # Output: 0.9 (consonantal match)

# Exact match
score = compare_hebrew('אהב', 'אהב')
print(score)  # Output: 1.0
```

## API Reference

### Core Functions

#### `normalize_hebrew(text: str) -> str`

Normalize Hebrew text to consonantal skeleton.

**Parameters:**
- `text` (str): Hebrew text (may include vowel points, final forms, etc.)

**Returns:**
- str: Normalized consonantal Hebrew text

**Example:**
```python
>>> normalize_hebrew('מֶלֶךְ')
'מלכ'
>>> normalize_hebrew('יְרוּשָׁלַיִם')
'ירושלימ'
```

#### `compare_hebrew(text1: str, text2: str, fuzzy: bool = True) -> float`

Compare two Hebrew texts and return similarity score.

**Parameters:**
- `text1` (str): First Hebrew text
- `text2` (str): Second Hebrew text
- `fuzzy` (bool): Enable fuzzy matching (default: True)

**Returns:**
- float: Similarity score from 0.0 (no match) to 1.0 (exact match)

**Scoring:**
- 1.0 = Exact match
- 0.9 = Consonantal match (after normalization)
- 0.85 = Spelling variant (plene vs. defective)
- 0.0-0.7 = Fuzzy match based on Levenshtein distance

**Example:**
```python
>>> compare_hebrew('אָהַב', 'אהב')
0.9
>>> compare_hebrew('דָּוִד', 'דָּוִיד')  # Spelling variant
0.85
```

#### `extract_strongs_hebrew(strongs_entry: dict, field: str = 'lemma') -> str`

Extract and normalize Hebrew text from Strong's Concordance entry.

**Parameters:**
- `strongs_entry` (dict): Strong's dictionary entry
- `field` (str): Field name to extract (default: 'lemma')

**Returns:**
- str: Normalized consonantal Hebrew text

**Example:**
```python
>>> entry = {'lemma': 'אָב', 'xlit': 'ʼâb', 'kjv_def': 'father'}
>>> extract_strongs_hebrew(entry)
'אב'
```

#### `extract_bhsa_hebrew(lex_node: int, F, field: str = 'voc_lex_utf8') -> str`

Extract and normalize Hebrew text from BHSA lexeme node.

**Parameters:**
- `lex_node` (int): BHSA lexeme node number
- `F`: Text-Fabric feature object
- `field` (str): Primary field to extract (default: 'voc_lex_utf8')

**Returns:**
- str: Normalized consonantal Hebrew text

**Example:**
```python
>>> # Assuming F is Text-Fabric feature object
>>> extract_bhsa_hebrew(12345, F)
'אב'
```

### Utility Functions

#### `is_hebrew_text(text: str) -> bool`

Check if text contains Hebrew characters.

#### `get_hebrew_stats(text: str) -> dict`

Get statistics about Hebrew text (consonants, vowel points, final forms, etc.).

#### `levenshtein_distance(s1: str, s2: str) -> int`

Calculate edit distance between two strings.

#### `remove_matres_lectionis(text: str) -> str`

Remove matres lectionis (vowel letters) for broader matching.

## Usage Examples

### Example 1: Normalize Strong's Entry

```python
from hebrew_normalizer import extract_strongs_hebrew, normalize_hebrew

# Strong's entry from JSON
strongs_entry = {
    'lemma': 'אָהַב',
    'xlit': 'ʼâhab',
    'pron': 'aw-hab',
    'kjv_def': 'love'
}

# Extract and normalize
normalized = extract_strongs_hebrew(strongs_entry)
print(f"Normalized: {normalized}")  # Output: אהב
```

### Example 2: Compare Strong's to BHSA

```python
from hebrew_normalizer import extract_strongs_hebrew, compare_hebrew

# Strong's entry
strongs = {'lemma': 'מֶלֶךְ'}
strongs_norm = extract_strongs_hebrew(strongs)

# BHSA data (consonantal)
bhsa_text = 'מלכ'

# Compare
score = compare_hebrew(strongs_norm, bhsa_text)
print(f"Match score: {score}")  # Output: 1.0 (perfect match)
```

### Example 3: Batch Processing

```python
from hebrew_normalizer import normalize_hebrew

# List of Hebrew words with niqqud
words = ['אָהַב', 'מֶלֶךְ', 'דָּוִד', 'תּוֹרָה']

# Normalize all
normalized = [normalize_hebrew(word) for word in words]
print(normalized)  # Output: ['אהב', 'מלכ', 'דוד', 'תורה']
```

### Example 4: Get Text Statistics

```python
from hebrew_normalizer import get_hebrew_stats

text = 'אָהַב'
stats = get_hebrew_stats(text)

print(f"Consonants: {stats['consonants']}")      # 3
print(f"Vowel points: {stats['vowel_points']}")  # 2
print(f"Has niqqud: {stats['has_niqqud']}")      # True
```

## Testing

Run the test suite:

```bash
# Using the simple test runner (no dependencies)
python3 run_tests.py

# Or using pytest (if installed)
pytest test_hebrew_normalizer.py -v
```

All tests should pass:
```
============================================================
Running Hebrew Normalizer Tests
============================================================

Testing normalize_hebrew...
✓ All normalize_hebrew tests passed!
Testing compare_hebrew...
✓ All compare_hebrew tests passed!
...
============================================================
✓ ALL TESTS PASSED!
============================================================
```

## Technical Details

### Unicode Ranges

- **Hebrew Letters**: U+05D0 to U+05EA (א-ת)
- **Niqqud (Vowel Points)**: U+05B0 to U+05BD, U+05BF to U+05C2, U+05C4 to U+05C5, U+05C7
- **Combining Characters**: Category 'Mn' (Mark, nonspacing)

### Final Form Mappings

| Final Form | Regular Form | Name |
|------------|--------------|------|
| ך | כ | Kaf |
| ם | מ | Mem |
| ן | נ | Nun |
| ף | פ | Pe |
| ץ | צ | Tsadi |

### Normalization Process

1. **Strip Combining Characters**: Remove all Unicode combining characters (niqqud, dagesh, etc.)
2. **Normalize Final Forms**: Convert final letter forms to regular forms
3. **Extract Hebrew Letters**: Keep only Hebrew letters (U+05D0-U+05EA)
4. **Return Consonantal Skeleton**: Pure consonantal Hebrew text

### Comparison Algorithm

1. **Exact Match**: If strings are identical → 1.0
2. **Normalize Both**: Apply normalization to both texts
3. **Consonantal Match**: If normalized forms match → 0.9
4. **Fuzzy Match**: Calculate Levenshtein distance → 0.0-0.7
5. **Spelling Variants**: Check for matres lectionis differences → 0.85

## Use Cases

### Strong's to BHSA Mapping

```python
# Map Strong's entries to BHSA lexemes
strongs_entries = load_strongs_data()  # Your data loading function
bhsa_lexemes = load_bhsa_data()        # Your data loading function

matches = []
for strongs in strongs_entries:
    strongs_norm = extract_strongs_hebrew(strongs)
    
    for bhsa in bhsa_lexemes:
        bhsa_norm = normalize_hebrew(bhsa['voc_lex_utf8'])
        score = compare_hebrew(strongs_norm, bhsa_norm)
        
        if score >= 0.9:  # High confidence match
            matches.append({
                'strongs_number': strongs['number'],
                'bhsa_lexeme': bhsa['lex_utf8'],
                'score': score
            })
```

### Fuzzy Search

```python
def find_similar_words(target, word_list, threshold=0.7):
    """Find words similar to target."""
    target_norm = normalize_hebrew(target)
    results = []
    
    for word in word_list:
        word_norm = normalize_hebrew(word)
        score = compare_hebrew(target_norm, word_norm)
        
        if score >= threshold:
            results.append((word, score))
    
    return sorted(results, key=lambda x: x[1], reverse=True)

# Example
similar = find_similar_words('אהב', ['אָהַב', 'אָהֵב', 'שָׁנָא'])
# Output: [('אָהַב', 1.0), ('אָהֵב', 0.9), ...]
```

## Limitations

1. **Mater Lectionis Detection**: The module uses a simplified approach for detecting matres lectionis (vowel letters). True detection requires morphological analysis.

2. **Homographs**: Words with identical consonantal forms but different meanings (e.g., מֶלֶךְ "king" vs. מָלַךְ "to reign") will match. Use part-of-speech or context for disambiguation.

3. **Proper Names**: Proper names may have unique spellings not found in lexicons. Handle separately.

4. **Aramaic vs. Hebrew**: The module treats Aramaic and Hebrew identically. Use language metadata for distinction.

## Contributing

Contributions welcome! Areas for improvement:
- More sophisticated mater lectionis detection
- Support for Qere/Ketiv variants
- Integration with morphological analyzers
- Performance optimization for large datasets

## License

This module is part of the Text-Fabric project and follows the same license.

## See Also

- [Strong's Concordance](https://github.com/openscriptures/strongs)
- [BHSA Dataset](https://github.com/ETCBC/bhsa)
- [Text-Fabric](https://annotation.github.io/text-fabric/)
- [Unicode Hebrew](https://unicode.org/charts/PDF/U0590.pdf)
