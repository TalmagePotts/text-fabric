# Strong's Search Library - Usage Examples

## Installation

The library is located in `strongs-mapping/strongs_search_lib.py` and requires the mapping data file.

```python
from strongs_search_lib import StrongsSearch

# Initialize (automatically finds mapping file)
search = StrongsSearch()
```

## Basic Searches

### Search by English Gloss

```python
# Exact match
results = search.search_by_gloss("love", exact=True)
for r in results:
    print(f"{r['hebrew']} ({r['strongs']}): {r['all_glosses']}")

# Output:
# רָחַם (H7355): have compassion on,upon,love,find,have,obtain,shew...
# אַהַב (H158): love...
# אֹהַב (H159): love...
```

```python
# Substring match (finds "beloved", "lover", etc.)
results = search.search_by_gloss("love", exact=False)
print(f"Found {len(results)} Hebrew words related to 'love'")
```

### Reverse Lookup (Strong's Number → Details)

```python
info = search.reverse_lookup("H157")
print(f"Hebrew: {info['hebrew']}")
print(f"Glosses: {info['kjv_glosses']}")
print(f"BHSA matches: {info['match_count']}")

# Output:
# Hebrew: אָהַב
# Glosses: love,lover,friend,beloved,like
# BHSA matches: 3
```

## Advanced Analysis

### Semantic Field Analysis

Find all Hebrew words that share an English translation:

```python
field = search.semantic_field("king")
print(f"Total Hebrew words for 'king': {field['total_words']}")
print(f"Most common: {field['most_common']['hebrew']} ({field['most_common']['occurrences']} times)")

for lexeme in field['lexeme_groups'][:5]:
    print(f"  {lexeme['hebrew']:15} - {lexeme['occurrences']} occurrences")
```

### Translation Variety

Find Hebrew words with the most diverse English translations:

```python
variety = search.translation_variety(10)
for hebrew, count, glosses, strongs in variety:
    print(f"{hebrew} ({strongs}): {count} different translations")
    print(f"  Glosses: {glosses[:60]}...")

# Output:
# שׁוּב (H7725): 79 different translations
#   Glosses: break,build,circumcise,dig,do anything,do,make again...
```

### Find Related Words

Find Hebrew words with similar English glosses:

```python
related = search.find_related_words("H157", max_results=5)
for r in related:
    print(f"{r['hebrew']} ({r['strongs']})")
    print(f"  Shared glosses: {', '.join(r['shared_glosses'])}")
    print(f"  Overlap: {r['overlap_score']*100:.0f}%")
```

### Compare Translations

Get all translation choices for a Hebrew word:

```python
trans = search.compare_translations("אהב")
if trans:
    print(f"Hebrew: {trans['hebrew']}")
    print(f"Strong's: {trans['strongs']}")
    print("KJV translations:")
    for gloss in trans['gloss_list']:
        print(f"  - {gloss}")
```

## Export Functions

### Export to CSV

```python
filename = search.export_lexicon('csv', 'my_lexicon.csv')
print(f"Exported to {filename}")
```

### Export to JSON

```python
filename = search.export_lexicon('json', 'my_lexicon.json')
```

### Export to Markdown

```python
filename = search.export_lexicon('markdown', 'lexicon.md')
```

## Statistics

```python
stats = search.statistics()
print(f"Total Strong's entries: {stats['total_strongs_entries']}")
print(f"Coverage: {stats['coverage']}%")
print(f"Unique English glosses: {stats['unique_english_glosses']}")
print(f"Average glosses per word: {stats['avg_glosses_per_word']}")
```

## Real-World Examples

### Find all words for "God"

```python
results = search.search_by_gloss("god", exact=False)
print(f"Found {len(results)} Hebrew words related to 'God':")
for r in results[:10]:
    print(f"  {r['hebrew']:15} ({r['strongs']:6}) - {r['matched_gloss']}")
```

### Analyze "love" semantic field

```python
field = search.semantic_field("love")
print(f"\nSemantic field for 'love':")
print(f"Total Hebrew words: {field['total_words']}")
print("\nMost frequent:")
for lex in field['lexeme_groups'][:5]:
    print(f"  {lex['hebrew']:15} - {lex['occurrences']} occurrences")
```

### Find words with most translation variety

```python
print("\nHebrew words with most diverse translations:")
variety = search.translation_variety(5)
for hebrew, count, glosses, strongs in variety:
    print(f"\n{hebrew} ({strongs}): {count} translations")
    print(f"  Sample: {glosses[:80]}...")
```

## Integration with Text-Fabric

If you have Text-Fabric with the Strong's module loaded:

```python
from tf.app import use
from strongs_search_lib import StrongsSearch

# Load BHSA with Strong's features
A = use('etcbc/bhsa', mod='TalmagePotts/strongs')
F = A.api.F

# Initialize search library
search = StrongsSearch()

# Find all occurrences of a word
results = search.search_by_gloss("love", exact=True)
for r in results:
    strongs_num = r['strongs']
    
    # Find all lexeme nodes with this Strong's number
    for lex_node in F.otype.s('lex'):
        if F.strongs.v(lex_node) == strongs_num:
            hebrew = F.voc_lex_utf8.v(lex_node)
            print(f"Found: {hebrew} ({strongs_num})")
            break
```

## Performance Notes

- Initial load: ~1 second (loads 8,674 Strong's entries)
- Index building: ~0.5 seconds (creates search indices)
- Search queries: < 0.01 seconds (indexed lookups)
- Export operations: ~1-2 seconds depending on format

## Coverage

- **Total Strong's entries**: 8,674
- **With BHSA matches**: 8,034 (92.6%)
- **High confidence**: 8,030
- **Unique English glosses**: 10,654
- **Average glosses per word**: 2.5
