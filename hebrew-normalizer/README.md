# Hebrew Text Normalizer

Python module for normalizing Hebrew text to facilitate matching between different Hebrew text sources.

## Contents

- **hebrew_normalizer.py** - Main normalization module
- **tests/** - Test suite
  - `test_hebrew_normalizer.py` - Pytest test suite
  - `run_tests.py` - Simple test runner (no dependencies)
- **docs/** - Documentation
  - `README_hebrew_normalizer.md` - Complete API documentation

## Quick Start

```python
from hebrew_normalizer import normalize_hebrew, compare_hebrew

# Normalize Hebrew text
text = 'אָהַב'  # "love" with vowel points
normalized = normalize_hebrew(text)
print(normalized)  # Output: 'אהב'

# Compare two Hebrew texts
score = compare_hebrew('אָהַב', 'אהב')
print(score)  # Output: 0.9 (consonantal match)
```

## Features

- Remove niqqud (vowel points)
- Normalize final letter forms
- Fuzzy matching with Levenshtein distance
- Extract from Strong's and BHSA formats
- No external dependencies

## Testing

```bash
python tests/run_tests.py
```

All tests pass ✓

## See Also

- [API Documentation](docs/README_hebrew_normalizer.md)
- [Strong's Mapping](../strongs-mapping/) - Uses this normalizer
