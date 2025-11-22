# Strong's Concordance Mapping for BHSA

Complete mapping between Strong's Hebrew Concordance and BHSA (Biblia Hebraica Stuttgartensia Amstelodamensis) lexemes.

## Contents

- **data/** - Mapping files and statistics
  - `strongs_to_bhsa.json` - Strong's → BHSA mapping (92.6% coverage)
  - `bhsa_to_strongs_complete.json` - BHSA → Strong's mapping (100% coverage)
  - `mapping_stats.txt` - Coverage statistics

- **scripts/** - Mapping generation scripts
  - `build_mapping.py` - Main mapping builder
  - `create_complete_bhsa_mapping.py` - Complete BHSA coverage
  - `apply_manual_corrections.py` - Manual corrections for particles

- **docs/** - Documentation
  - `README_mapping.md` - Detailed mapping documentation
  - `mapping_spec.json` - Mapping specification

- **features/** - Text-Fabric feature files (generated)

## Quick Start

```python
import json

# Load Strong's → BHSA mapping
with open('data/strongs_to_bhsa.json') as f:
    mapping = json.load(f)

# Get BHSA matches for Strong's H157 (love)
entry = mapping['H157']
print(f"Hebrew: {entry['strongs_lemma']}")
print(f"Matches: {len(entry['bhsa_matches'])}")
print(f"KJV glosses: {entry['kjv_glosses']}")
```

## Coverage

- **Strong's → BHSA**: 8,034/8,674 (92.6%)
- **BHSA → Strong's**: 8,091/8,091 (100%)

## See Also

- [Hebrew Normalizer](../hebrew-normalizer/) - Text normalization functions
- [Mapping Documentation](docs/README_mapping.md) - Detailed guide
