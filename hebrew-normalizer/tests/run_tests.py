"""
Simple test runner for Hebrew normalizer (no pytest required)
Run with: python3 run_tests.py
"""

from hebrew_normalizer import (
    normalize_hebrew,
    compare_hebrew,
    extract_strongs_hebrew,
    is_hebrew_text,
    get_hebrew_stats,
    levenshtein_distance,
)


def test_normalize_hebrew():
    """Test Hebrew normalization."""
    print("Testing normalize_hebrew...")
    
    # Test niqqud removal
    assert normalize_hebrew('אָהַב') == 'אהב', "Failed: niqqud removal"
    assert normalize_hebrew('מֶלֶךְ') == 'מלכ', "Failed: niqqud removal with final form"
    assert normalize_hebrew('דָּוִד') == 'דוד', "Failed: dagesh removal"
    
    # Test final forms
    assert normalize_hebrew('מלך') == 'מלכ', "Failed: final kaf"
    assert normalize_hebrew('שלום') == 'שלומ', "Failed: final mem"
    assert normalize_hebrew('אדון') == 'אדונ', "Failed: final nun"
    assert normalize_hebrew('יוסף') == 'יוספ', "Failed: final pe"
    assert normalize_hebrew('ארץ') == 'ארצ', "Failed: final tsadi"
    
    # Test empty string
    assert normalize_hebrew('') == '', "Failed: empty string"
    
    # Test complex text
    assert normalize_hebrew('יְרוּשָׁלַיִם') == 'ירושלימ', "Failed: Jerusalem"
    assert normalize_hebrew('תּוֹרָה') == 'תורה', "Failed: Torah"
    
    print("✓ All normalize_hebrew tests passed!")


def test_compare_hebrew():
    """Test Hebrew comparison."""
    print("Testing compare_hebrew...")
    
    # Exact match
    assert compare_hebrew('אהב', 'אהב') == 1.0, "Failed: exact match"
    
    # Consonantal match
    score = compare_hebrew('אָהַב', 'אהב')
    assert score == 0.9, f"Failed: consonantal match (got {score})"
    
    score = compare_hebrew('מֶלֶךְ', 'מלך')
    assert score == 0.9, f"Failed: consonantal match with final form (got {score})"
    
    # Empty strings
    assert compare_hebrew('', '') == 0.0, "Failed: empty strings"
    assert compare_hebrew('אהב', '') == 0.0, "Failed: one empty string"
    
    # Different words
    score = compare_hebrew('אהב', 'שנא')
    assert score < 0.5, f"Failed: different words should have low score (got {score})"
    
    print("✓ All compare_hebrew tests passed!")


def test_extract_strongs_hebrew():
    """Test Strong's extraction."""
    print("Testing extract_strongs_hebrew...")
    
    # Standard entry
    entry = {'lemma': 'אָב', 'xlit': 'ʼâb', 'kjv_def': 'father'}
    assert extract_strongs_hebrew(entry) == 'אב', "Failed: standard entry"
    
    # With final forms
    entry = {'lemma': 'מֶלֶךְ'}
    assert extract_strongs_hebrew(entry) == 'מלכ', "Failed: final forms"
    
    # Empty entry
    assert extract_strongs_hebrew({}) == '', "Failed: empty entry"
    assert extract_strongs_hebrew(None) == '', "Failed: None entry"
    
    # Alternative field names
    entry = {'hebrew': 'אָהַב'}
    assert extract_strongs_hebrew(entry) == 'אהב', "Failed: alternative field"
    
    print("✓ All extract_strongs_hebrew tests passed!")


def test_is_hebrew_text():
    """Test Hebrew detection."""
    print("Testing is_hebrew_text...")
    
    assert is_hebrew_text('אהב') is True, "Failed: Hebrew text"
    assert is_hebrew_text('אָהַב') is True, "Failed: Hebrew with niqqud"
    assert is_hebrew_text('hello') is False, "Failed: English text"
    assert is_hebrew_text('123') is False, "Failed: numbers"
    assert is_hebrew_text('') is False, "Failed: empty string"
    assert is_hebrew_text('hello אהב world') is True, "Failed: mixed text"
    
    print("✓ All is_hebrew_text tests passed!")


def test_get_hebrew_stats():
    """Test Hebrew statistics."""
    print("Testing get_hebrew_stats...")
    
    # Consonants only
    stats = get_hebrew_stats('אהב')
    assert stats['consonants'] == 3, "Failed: consonant count"
    assert stats['vowel_points'] == 0, "Failed: no vowel points"
    assert stats['has_niqqud'] is False, "Failed: no niqqud flag"
    
    # With niqqud
    stats = get_hebrew_stats('אָהַב')
    assert stats['consonants'] == 3, "Failed: consonant count with niqqud"
    assert stats['vowel_points'] > 0, "Failed: vowel point count"
    assert stats['has_niqqud'] is True, "Failed: has niqqud flag"
    
    # Final forms
    stats = get_hebrew_stats('מלך')
    assert stats['final_forms'] == 1, "Failed: final form count"
    
    print("✓ All get_hebrew_stats tests passed!")


def test_levenshtein_distance():
    """Test Levenshtein distance."""
    print("Testing levenshtein_distance...")
    
    assert levenshtein_distance('אהב', 'אהב') == 0, "Failed: identical strings"
    assert levenshtein_distance('אהב', 'אהד') == 1, "Failed: one char difference"
    assert levenshtein_distance('', '') == 0, "Failed: empty strings"
    assert levenshtein_distance('abc', '') == 3, "Failed: empty vs non-empty"
    
    print("✓ All levenshtein_distance tests passed!")


def test_integration():
    """Integration tests."""
    print("Testing integration scenarios...")
    
    # Strong's to BHSA workflow
    strongs_entry = {'lemma': 'אָהַב', 'kjv_def': 'love'}
    strongs_normalized = extract_strongs_hebrew(strongs_entry)
    bhsa_text = 'אהב'
    score = compare_hebrew(strongs_normalized, bhsa_text)
    assert score == 1.0, f"Failed: Strong's to BHSA workflow (got {score})"
    
    # Multiple entries
    entries = [
        {'lemma': 'אָב'},
        {'lemma': 'אָהַב'},
        {'lemma': 'מֶלֶךְ'},
    ]
    
    for entry in entries:
        normalized = extract_strongs_hebrew(entry)
        assert len(normalized) > 0, f"Failed: empty normalization for {entry}"
        assert is_hebrew_text(normalized), f"Failed: not Hebrew text for {entry}"
    
    print("✓ All integration tests passed!")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Hebrew Normalizer Tests")
    print("=" * 60)
    print()
    
    try:
        test_normalize_hebrew()
        test_compare_hebrew()
        test_extract_strongs_hebrew()
        test_is_hebrew_text()
        test_get_hebrew_stats()
        test_levenshtein_distance()
        test_integration()
        
        print()
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ ERROR: {e}")
        print("=" * 60)
        return False


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
