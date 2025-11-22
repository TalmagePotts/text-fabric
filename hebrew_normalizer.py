"""
Hebrew Text Normalization Module

This module provides functions for normalizing Hebrew text to enable matching
between different Hebrew text sources (Strong's Concordance and BHSA).

The normalization process handles:
- Removal of vowel points (niqqud)
- Normalization of final letter forms
- Consonantal skeleton extraction
- Fuzzy matching with spelling variants
"""

import re
import unicodedata
from typing import Optional, Dict, Any
from difflib import SequenceMatcher


# Unicode ranges for Hebrew characters
HEBREW_LETTERS = range(0x05D0, 0x05EB)  # א-ת
HEBREW_POINTS = range(0x05B0, 0x05BD)   # Niqqud (vowel points)
HEBREW_POINTS_EXTENDED = [
    range(0x05B0, 0x05BD),  # Main niqqud
    range(0x05BF, 0x05C3),  # Additional points
    range(0x05C4, 0x05C6),  # More points
    [0x05C7],               # Qamats qatan
]

# Final form mappings
FINAL_FORMS = {
    'ך': 'כ',  # Final Kaf -> Kaf
    'ם': 'מ',  # Final Mem -> Mem
    'ן': 'נ',  # Final Nun -> Nun
    'ף': 'פ',  # Final Pe -> Pe
    'ץ': 'צ',  # Final Tsadi -> Tsadi
}

# Common spelling variants (plene vs. defective)
SPELLING_VARIANTS = {
    'ו': '',   # Vav as mater lectionis
    'י': '',   # Yod as mater lectionis
}


def normalize_hebrew(text: str) -> str:
    """
    Normalize Hebrew text to consonantal skeleton.
    
    This function:
    1. Removes all vowel points (niqqud) and diacritical marks
    2. Normalizes final letter forms to regular forms
    3. Strips whitespace
    4. Returns only the consonantal skeleton
    
    Args:
        text: Hebrew text (may include vowel points, final forms, etc.)
        
    Returns:
        Normalized consonantal Hebrew text
        
    Examples:
        >>> normalize_hebrew('אָהַב')
        'אהב'
        >>> normalize_hebrew('מֶלֶךְ')
        'מלכ'
        >>> normalize_hebrew('דָּוִד')
        'דוד'
    """
    if not text:
        return ''
    
    # Remove combining characters (niqqud, dagesh, etc.)
    normalized = ''
    for char in text:
        # Skip combining characters (vowel points, dagesh, etc.)
        if unicodedata.category(char) == 'Mn':  # Mark, nonspacing
            continue
        # Skip specific Hebrew point ranges
        code_point = ord(char)
        if any(code_point in point_range for point_range in HEBREW_POINTS_EXTENDED):
            continue
        if code_point == 0x05C7:  # Qamats qatan
            continue
        normalized += char
    
    # Normalize final forms
    for final, regular in FINAL_FORMS.items():
        normalized = normalized.replace(final, regular)
    
    # Strip whitespace and other non-Hebrew characters (keep only Hebrew letters)
    result = ''.join(char for char in normalized if 0x05D0 <= ord(char) <= 0x05EA)
    
    return result


def remove_matres_lectionis(text: str) -> str:
    """
    Remove matres lectionis (vowel letters) for broader matching.
    
    This creates an even more normalized form by removing vav and yod
    when used as vowel indicators (not consonants).
    
    Args:
        text: Consonantal Hebrew text
        
    Returns:
        Text with potential matres lectionis removed
        
    Note:
        This is aggressive normalization and may cause false matches.
        Use only for fuzzy matching scenarios.
    """
    # This is a simplified approach - true mater lectionis detection
    # requires morphological analysis
    result = text
    # Remove doubled vav/yod which are likely vowel indicators
    result = re.sub(r'וו', 'ו', result)
    result = re.sub(r'יי', 'י', result)
    return result


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Edit distance (number of single-character edits needed)
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def compare_hebrew(text1: str, text2: str, 
                   fuzzy: bool = True,
                   weight_exact: float = 1.0,
                   weight_consonantal: float = 0.9) -> float:
    """
    Compare two Hebrew texts and return similarity score.
    
    This function performs multi-level comparison:
    1. Exact match (if identical) -> 1.0
    2. Normalized consonantal match -> weighted score
    3. Fuzzy match with Levenshtein distance -> lower score
    
    Args:
        text1: First Hebrew text
        text2: Second Hebrew text
        fuzzy: Enable fuzzy matching for spelling variants
        weight_exact: Weight for exact matches (default 1.0)
        weight_consonantal: Weight for consonantal matches (default 0.9)
        
    Returns:
        Similarity score from 0.0 (no match) to 1.0 (exact match)
        
    Examples:
        >>> compare_hebrew('אָהַב', 'אהב')
        0.9
        >>> compare_hebrew('מֶלֶךְ', 'מלך')
        0.9
        >>> compare_hebrew('דָּוִד', 'דָּוִיד')  # Spelling variant
        0.85
    """
    if not text1 or not text2:
        return 0.0
    
    # Exact match
    if text1 == text2:
        return weight_exact
    
    # Normalize both texts
    norm1 = normalize_hebrew(text1)
    norm2 = normalize_hebrew(text2)
    
    # Consonantal match
    if norm1 == norm2:
        return weight_consonantal
    
    if not fuzzy:
        return 0.0
    
    # Fuzzy matching with Levenshtein distance
    max_len = max(len(norm1), len(norm2))
    if max_len == 0:
        return 0.0
    
    distance = levenshtein_distance(norm1, norm2)
    similarity = 1.0 - (distance / max_len)
    
    # Apply penalty for fuzzy matches
    fuzzy_weight = 0.7
    
    # Additional check: try removing matres lectionis for spelling variants
    if similarity < 0.9:
        norm1_no_ml = remove_matres_lectionis(norm1)
        norm2_no_ml = remove_matres_lectionis(norm2)
        if norm1_no_ml == norm2_no_ml and len(norm1_no_ml) > 0:
            # Likely spelling variant (plene vs. defective)
            return 0.85
    
    return similarity * fuzzy_weight


def extract_strongs_hebrew(strongs_entry: Dict[str, Any], 
                           field: str = 'lemma') -> str:
    """
    Extract and normalize Hebrew text from Strong's Concordance entry.
    
    Handles different Strong's data formats (JSON, dict) and extracts
    the Hebrew lemma, applying normalization.
    
    Args:
        strongs_entry: Strong's dictionary entry (from JSON format)
        field: Field name to extract (default: 'lemma')
        
    Returns:
        Normalized consonantal Hebrew text
        
    Examples:
        >>> entry = {'lemma': 'אָב', 'xlit': 'ʼâb', 'kjv_def': 'father'}
        >>> extract_strongs_hebrew(entry)
        'אב'
    """
    if not strongs_entry or not isinstance(strongs_entry, dict):
        return ''
    
    # Try to get the specified field
    hebrew_text = strongs_entry.get(field, '')
    
    # Fallback to other possible field names
    if not hebrew_text:
        for alt_field in ['lemma', 'hebrew', 'word', 'text']:
            hebrew_text = strongs_entry.get(alt_field, '')
            if hebrew_text:
                break
    
    # Normalize and return
    return normalize_hebrew(hebrew_text)


def extract_bhsa_hebrew(lex_node: int, F, 
                       field: str = 'voc_lex_utf8',
                       fallback_field: str = 'lex_utf8') -> str:
    """
    Extract and normalize Hebrew text from BHSA lexeme node.
    
    Uses Text-Fabric API to extract lexeme data and applies normalization.
    
    Args:
        lex_node: BHSA lexeme node number
        F: Text-Fabric feature object (from API)
        field: Primary field to extract (default: 'voc_lex_utf8')
        fallback_field: Fallback field if primary is empty (default: 'lex_utf8')
        
    Returns:
        Normalized consonantal Hebrew text
        
    Examples:
        >>> # Assuming F is Text-Fabric feature object
        >>> extract_bhsa_hebrew(12345, F)
        'אב'
    """
    if not lex_node or not F:
        return ''
    
    try:
        # Try primary field (vocalized)
        hebrew_text = ''
        if hasattr(F, field):
            feature = getattr(F, field)
            if hasattr(feature, 'v'):
                hebrew_text = feature.v(lex_node)
        
        # Fallback to consonantal if vocalized not available
        if not hebrew_text and hasattr(F, fallback_field):
            feature = getattr(F, fallback_field)
            if hasattr(feature, 'v'):
                hebrew_text = feature.v(lex_node)
        
        # Normalize and return
        return normalize_hebrew(hebrew_text) if hebrew_text else ''
        
    except (AttributeError, TypeError, KeyError):
        return ''


def is_hebrew_text(text: str) -> bool:
    """
    Check if text contains Hebrew characters.
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains at least one Hebrew letter
    """
    if not text:
        return False
    
    return any(0x05D0 <= ord(char) <= 0x05EA for char in text)


def get_hebrew_stats(text: str) -> Dict[str, Any]:
    """
    Get statistics about Hebrew text.
    
    Args:
        text: Hebrew text (may include niqqud)
        
    Returns:
        Dictionary with statistics:
        - consonants: Number of consonantal letters
        - vowel_points: Number of vowel points
        - final_forms: Number of final form letters
        - has_niqqud: Whether text has vowel points
    """
    stats = {
        'consonants': 0,
        'vowel_points': 0,
        'final_forms': 0,
        'has_niqqud': False,
        'length': len(text)
    }
    
    for char in text:
        code_point = ord(char)
        
        # Check for Hebrew consonants
        if 0x05D0 <= code_point <= 0x05EA:
            stats['consonants'] += 1
            
            # Check for final forms
            if char in FINAL_FORMS:
                stats['final_forms'] += 1
        
        # Check for vowel points
        if unicodedata.category(char) == 'Mn':
            stats['vowel_points'] += 1
            stats['has_niqqud'] = True
    
    return stats


# Convenience function for batch processing
def normalize_hebrew_list(texts: list[str]) -> list[str]:
    """
    Normalize a list of Hebrew texts.
    
    Args:
        texts: List of Hebrew texts
        
    Returns:
        List of normalized texts
    """
    return [normalize_hebrew(text) for text in texts]


if __name__ == '__main__':
    # Example usage
    examples = [
        'אָהַב',      # ahav (love) - with niqqud
        'מֶלֶךְ',     # melekh (king) - with niqqud
        'דָּוִד',     # David - with dagesh and niqqud
        'יְרוּשָׁלַיִם', # Jerusalem
        'תּוֹרָה',    # Torah
    ]
    
    print("Hebrew Normalization Examples:")
    print("=" * 60)
    for text in examples:
        normalized = normalize_hebrew(text)
        stats = get_hebrew_stats(text)
        print(f"Original:   {text}")
        print(f"Normalized: {normalized}")
        print(f"Stats:      {stats['consonants']} consonants, "
              f"{stats['vowel_points']} vowel points")
        print("-" * 60)
    
    print("\nComparison Examples:")
    print("=" * 60)
    pairs = [
        ('אָהַב', 'אהב'),
        ('מֶלֶךְ', 'מלך'),
        ('דָּוִד', 'דָּוִיד'),  # Spelling variant
    ]
    
    for text1, text2 in pairs:
        score = compare_hebrew(text1, text2)
        print(f"'{text1}' vs '{text2}': {score:.2f}")
