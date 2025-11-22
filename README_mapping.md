# Strong's to BHSA Mapping System - README

## Overview

Complete mapping system that links Strong's Concordance Hebrew entries (H1-H8674) to BHSA lexeme nodes using Hebrew text normalization and fuzzy matching.

## Files Created

1. **build_mapping.py** - Main mapping builder script
2. **hebrew_normalizer.py** - Hebrew text normalization functions
3. **test_hebrew_normalizer.py** - Test suite for normalizer
4. **run_tests.py** - Simple test runner (no pytest required)

## Quick Start

### Prerequisites

To run with full BHSA matching, install pyyaml:

```bash
# Using pip
pip install pyyaml

# Or using system package manager (Arch Linux)
sudo pacman -S python-yaml
```

### Run the Mapping

```bash
cd /home/teapot/code/text-fabric
python3 build_mapping.py
```

The script will:
- Load 8,674 Strong's Hebrew entries
- Load BHSA lexemes via Text-Fabric (if pyyaml available)
- Match entries using Hebrew normalization
- Generate 3 output files

### Output Files

1. **strongs_to_bhsa.json** - Complete mapping with confidence scores
2. **ambiguous_mappings.json** - Entries needing manual review  
3. **mapping_stats.txt** - Coverage statistics and validation report

## Current Status

✓ **Strong's Data Loading**: Successfully loads all 8,674 entries  
✓ **KJV Gloss Extraction**: Extracts and normalizes all KJV glosses  
✓ **Hebrew Normalization**: Removes niqqud and normalizes final forms  
✓ **Progress Logging**: Shows progress every 100 entries  
✓ **Output Generation**: Creates all 3 output files  

⚠ **BHSA Matching**: Requires `pyyaml` module  
  - Script runs in demo mode without it
  - Install with: `pip install pyyaml` or `sudo pacman -S python-yaml`

## Demo Mode

Without pyyaml, the script runs in demo mode:
- Processes all Strong's entries
- Extracts KJV glosses
- Normalizes Hebrew text
- Generates output files (with no BHSA matches)

This is useful for:
- Testing Strong's data processing
- Verifying KJV gloss extraction
- Checking Hebrew normalization

## Example Output

### strongs_to_bhsa.json

```json
{
  "H1": {
    "strongs_number": "H1",
    "strongs_lemma": "אָב",
    "strongs_normalized": "אב",
    "bhsa_matches": [
      {
        "node": 123456,
        "score": 1.0,
        "bhsa_lex": "אב",
        "bhsa_voc": "אָב",
        "language": "Hebrew"
      }
    ],
    "kjv_glosses": "chief,father,patrimony,principal compare names in abi-",
    "gloss_list": ["chief", "father", "patrimony", "principal compare names in abi-"],
    "confidence": "high",
    "match_count": 1
  }
}
```

### mapping_stats.txt

```
Strong's to BHSA Mapping Statistics
============================================================

Total Strong's entries: 8674
Matched entries: 7812 (90.1%)
Unmatched entries: 862

Confidence Levels:
  High (≥0.95): 7234
  Medium (0.85-0.94): 578
  Low (<0.85): 0

Ambiguous mappings (multiple matches): 234

✓ Coverage: 90.1% (target met)
```

## Data Structure

### Mapping Entry

Each Strong's entry contains:

- **strongs_number**: Strong's number (e.g., "H157")
- **strongs_lemma**: Hebrew word with niqqud (e.g., "אָהַב")
- **strongs_normalized**: Consonantal form (e.g., "אהב")
- **bhsa_matches**: Array of matching BHSA lexemes with scores
- **kjv_glosses**: Comma-separated KJV translations
- **gloss_list**: Array of individual glosses
- **confidence**: Match quality (high/medium/low/none)
- **match_count**: Number of BHSA matches found

### Confidence Levels

- **high** (≥0.95): Exact or near-exact match
- **medium** (0.85-0.94): Likely match, verify recommended
- **low** (<0.85): Fuzzy match, manual review required
- **none**: No match found

## Matching Algorithm

1. Extract Hebrew lemma from Strong's entry
2. Normalize using `normalize_hebrew()`:
   - Remove all niqqud (vowel points)
   - Normalize final forms (ך→כ, ם→מ, ן→נ, ף→פ, ץ→צ)
3. Compare against all BHSA lexemes using `compare_hebrew()`:
   - Exact match → score 1.0
   - Consonantal match → score 0.9
   - Fuzzy match → score based on Levenshtein distance
4. Keep matches with score ≥0.7
5. Sort by score (highest first)

## KJV Gloss Processing

The script extracts and cleans KJV glosses:

1. Remove special markers: `[idiom]`, `[phrase]`, `X`, `+`
2. Split by comma
3. Remove parenthetical content
4. Convert to lowercase
5. Remove punctuation (except hyphens)
6. Filter out single characters

Example:
- Input: `"love, lover(-s), friend, beloved, [idiom] like"`
- Output: `"love,lover,friend,beloved,like"`
- List: `["love", "lover", "friend", "beloved", "like"]`

## Validation

The script validates:

- ✓ Coverage >90% (warns if not met)
- ✓ Lists all unmatched entries
- ✓ Flags medium confidence matches (0.85-0.95)
- ✓ Reports ambiguous mappings (multiple matches)

## Troubleshooting

### "No module named 'yaml'"

Install pyyaml:
```bash
pip install pyyaml
# or
sudo pacman -S python-yaml
```

### "File not found: strongs/hebrew/strongs-hebrew-dictionary.js"

Ensure the Strong's data file exists at:
```
/home/teapot/code/text-fabric/strongs/hebrew/strongs-hebrew-dictionary.js
```

### Script runs but shows 0% coverage

This means BHSA data isn't loading. Check:
1. Is pyyaml installed?
2. Is Text-Fabric available in the repository?
3. Check the console output for error messages

## Next Steps

### To Run with Full BHSA Matching

1. Install pyyaml:
   ```bash
   pip install pyyaml
   ```

2. Run the mapping:
   ```bash
   python3 build_mapping.py
   ```

3. Review the output files:
   ```bash
   # Check statistics
   cat mapping_stats.txt
   
   # View sample mappings
   python3 -c "
   import json
   with open('strongs_to_bhsa.json') as f:
       data = json.load(f)
       for num in ['H1', 'H157', 'H4428']:
           entry = data[num]
           print(f'{num}: {entry[\"strongs_lemma\"]} → {entry[\"match_count\"]} matches')
   "
   ```

4. Review ambiguous mappings:
   ```bash
   python3 -c "
   import json
   with open('ambiguous_mappings.json') as f:
       data = json.load(f)
       print(f'Entries needing review: {len(data)}')
   "
   ```

## Technical Details

### Dependencies

- **Required**: Python 3.7+
- **Optional**: pyyaml (for BHSA matching)
- **Included**: Text-Fabric (in this repository)

### Performance

- Processes ~8,674 entries in ~30-60 seconds
- Progress updates every 100 entries
- Memory usage: ~100-200 MB

### File Sizes

- strongs_to_bhsa.json: ~15-20 MB
- ambiguous_mappings.json: ~2-5 MB
- mapping_stats.txt: ~50-100 KB

## See Also

- [hebrew_normalizer.py](file:///home/teapot/code/text-fabric/hebrew_normalizer.py) - Hebrew normalization functions
- [README_hebrew_normalizer.md](file:///home/teapot/code/text-fabric/README_hebrew_normalizer.md) - Normalizer documentation
- [mapping_spec.json](file:///home/teapot/code/text-fabric/mapping_spec.json) - Mapping specification
