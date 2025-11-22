"""
Tests for Hebrew Text Normalization Module

Run with: pytest test_hebrew_normalizer.py -v
"""

import pytest
from hebrew_normalizer import (
    normalize_hebrew,
    compare_hebrew,
    extract_strongs_hebrew,
    is_hebrew_text,
    get_hebrew_stats,
    levenshtein_distance,
    remove_matres_lectionis,
)


class TestNormalizeHebrew:
    """Test cases for normalize_hebrew function."""
    
    def test_remove_niqqud(self):
        """Test removal of vowel points (niqqud)."""
        assert normalize_hebrew('אָהַב') == 'אהב'
        assert normalize_hebrew('מֶלֶךְ') == 'מלכ'
        assert normalize_hebrew('דָּוִד') == 'דוד'
    
    def test_final_forms(self):
        """Test normalization of final letter forms."""
        assert normalize_hebrew('מֶלֶךְ') == 'מלכ'  # ך -> כ
        assert normalize_hebrew('שָׁלוֹם') == 'שלומ'  # ם -> מ
        assert normalize_hebrew('אָדוֹן') == 'אדונ'  # ן -> נ
        assert normalize_hebrew('יוֹסֵף') == 'יוספ'  # ף -> פ
        assert normalize_hebrew('אֶרֶץ') == 'ארצ'   # ץ -> צ
    
    def test_empty_string(self):
        """Test handling of empty string."""
        assert normalize_hebrew('') == ''
        assert normalize_hebrew(None) == ''
    
    def test_already_normalized(self):
        """Test text that is already in consonantal form."""
        assert normalize_hebrew('אהב') == 'אהב'
        assert normalize_hebrew('מלכ') == 'מלכ'
    
    def test_mixed_content(self):
        """Test text with mixed Hebrew and non-Hebrew content."""
        # Should extract only Hebrew letters
        assert normalize_hebrew('אָב 123') == 'אב'
        assert normalize_hebrew('test אָב test') == 'אב'
    
    def test_complex_niqqud(self):
        """Test removal of various niqqud marks."""
        # Qamats, patach, segol, etc.
        assert normalize_hebrew('יְרוּשָׁלַיִם') == 'ירושלימ'
        assert normalize_hebrew('תּוֹרָה') == 'תורה'
        assert normalize_hebrew('בְּרֵאשִׁית') == 'בראשית'
    
    def test_dagesh(self):
        """Test removal of dagesh (dot in letter)."""
        assert normalize_hebrew('דָּוִד') == 'דוד'
        assert normalize_hebrew('שַׁבָּת') == 'שבת'


class TestCompareHebrew:
    """Test cases for compare_hebrew function."""
    
    def test_exact_match(self):
        """Test exact string matches."""
        assert compare_hebrew('אהב', 'אהב') == 1.0
        assert compare_hebrew('מלך', 'מלך') == 1.0
    
    def test_consonantal_match(self):
        """Test matches after normalization."""
        score = compare_hebrew('אָהַב', 'אהב')
        assert score == 0.9  # Consonantal match weight
        
        score = compare_hebrew('מֶלֶךְ', 'מלך')
        assert score == 0.9
    
    def test_spelling_variants(self):
        """Test handling of plene vs. defective spelling."""
        # These should have high similarity
        score = compare_hebrew('דָּוִד', 'דָּוִיד')
        assert score >= 0.7  # Should recognize as similar
    
    def test_no_match(self):
        """Test completely different words."""
        score = compare_hebrew('אהב', 'שנא')
        assert score < 0.5  # Should be low similarity
    
    def test_empty_strings(self):
        """Test handling of empty strings."""
        assert compare_hebrew('', '') == 0.0
        assert compare_hebrew('אהב', '') == 0.0
        assert compare_hebrew('', 'אהב') == 0.0
    
    def test_fuzzy_matching(self):
        """Test fuzzy matching with small differences."""
        # One character difference
        score = compare_hebrew('אהב', 'אהד', fuzzy=True)
        assert 0.0 < score < 0.9
        
        # Fuzzy disabled
        score = compare_hebrew('אהב', 'אהד', fuzzy=False)
        assert score == 0.0
    
    def test_final_forms_match(self):
        """Test that final forms match their regular counterparts."""
        score = compare_hebrew('מלך', 'מלכ')
        assert score == 1.0  # Should normalize and match


class TestExtractStrongsHebrew:
    """Test cases for extract_strongs_hebrew function."""
    
    def test_standard_entry(self):
        """Test extraction from standard Strong's entry."""
        entry = {
            'lemma': 'אָב',
            'xlit': 'ʼâb',
            'pron': 'awb',
            'kjv_def': 'father'
        }
        assert extract_strongs_hebrew(entry) == 'אב'
    
    def test_with_final_forms(self):
        """Test extraction with final forms."""
        entry = {'lemma': 'מֶלֶךְ'}
        assert extract_strongs_hebrew(entry) == 'מלכ'
    
    def test_empty_entry(self):
        """Test handling of empty or invalid entries."""
        assert extract_strongs_hebrew({}) == ''
        assert extract_strongs_hebrew(None) == ''
        assert extract_strongs_hebrew({'other': 'data'}) == ''
    
    def test_alternative_field_names(self):
        """Test fallback to alternative field names."""
        entry = {'hebrew': 'אָהַב'}
        assert extract_strongs_hebrew(entry) == 'אהב'
        
        entry = {'word': 'דָּוִד'}
        assert extract_strongs_hebrew(entry) == 'דוד'
    
    def test_custom_field(self):
        """Test extraction from custom field."""
        entry = {'custom_field': 'תּוֹרָה', 'lemma': 'other'}
        assert extract_strongs_hebrew(entry, field='custom_field') == 'תורה'


class TestIsHebrewText:
    """Test cases for is_hebrew_text function."""
    
    def test_hebrew_text(self):
        """Test detection of Hebrew text."""
        assert is_hebrew_text('אהב') is True
        assert is_hebrew_text('אָהַב') is True
        assert is_hebrew_text('שָׁלוֹם') is True
    
    def test_non_hebrew_text(self):
        """Test detection of non-Hebrew text."""
        assert is_hebrew_text('hello') is False
        assert is_hebrew_text('123') is False
        assert is_hebrew_text('') is False
        assert is_hebrew_text(None) is False
    
    def test_mixed_text(self):
        """Test detection in mixed text."""
        assert is_hebrew_text('hello אהב world') is True
        assert is_hebrew_text('123 שלום 456') is True


class TestGetHebrewStats:
    """Test cases for get_hebrew_stats function."""
    
    def test_consonants_count(self):
        """Test counting of consonants."""
        stats = get_hebrew_stats('אהב')
        assert stats['consonants'] == 3
        assert stats['vowel_points'] == 0
        assert stats['has_niqqud'] is False
    
    def test_with_niqqud(self):
        """Test counting with niqqud."""
        stats = get_hebrew_stats('אָהַב')
        assert stats['consonants'] == 3
        assert stats['vowel_points'] > 0
        assert stats['has_niqqud'] is True
    
    def test_final_forms_count(self):
        """Test counting of final forms."""
        stats = get_hebrew_stats('מלך')
        assert stats['final_forms'] == 1  # ך
        
        stats = get_hebrew_stats('שלום')
        assert stats['final_forms'] == 1  # ם
    
    def test_empty_text(self):
        """Test stats for empty text."""
        stats = get_hebrew_stats('')
        assert stats['consonants'] == 0
        assert stats['vowel_points'] == 0
        assert stats['length'] == 0


class TestLevenshteinDistance:
    """Test cases for levenshtein_distance function."""
    
    def test_identical_strings(self):
        """Test distance for identical strings."""
        assert levenshtein_distance('אהב', 'אהב') == 0
        assert levenshtein_distance('test', 'test') == 0
    
    def test_one_character_difference(self):
        """Test distance for one character difference."""
        assert levenshtein_distance('אהב', 'אהד') == 1
        assert levenshtein_distance('cat', 'bat') == 1
    
    def test_empty_strings(self):
        """Test distance with empty strings."""
        assert levenshtein_distance('', '') == 0
        assert levenshtein_distance('abc', '') == 3
        assert levenshtein_distance('', 'abc') == 3
    
    def test_completely_different(self):
        """Test distance for completely different strings."""
        dist = levenshtein_distance('אהב', 'שנא')
        assert dist == 3  # All characters different


class TestRemoveMatresLectionis:
    """Test cases for remove_matres_lectionis function."""
    
    def test_doubled_vav(self):
        """Test removal of doubled vav."""
        assert remove_matres_lectionis('קוום') == 'קום'
    
    def test_doubled_yod(self):
        """Test removal of doubled yod."""
        assert remove_matres_lectionis('שיים') == 'שים'
    
    def test_no_change(self):
        """Test text without matres lectionis."""
        assert remove_matres_lectionis('אהב') == 'אהב'
        assert remove_matres_lectionis('מלכ') == 'מלכ'


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_unicode_normalization(self):
        """Test handling of different Unicode normalizations."""
        # NFD vs NFC forms should both work
        text_nfc = 'אָב'
        text_nfd = 'אָב'  # Decomposed form
        
        norm_nfc = normalize_hebrew(text_nfc)
        norm_nfd = normalize_hebrew(text_nfd)
        
        # Both should produce same result
        assert norm_nfc == norm_nfd
    
    def test_non_string_input(self):
        """Test handling of non-string input."""
        assert normalize_hebrew(None) == ''
        # Numbers and other types should be handled gracefully
    
    def test_very_long_text(self):
        """Test handling of long text."""
        long_text = 'אָהַב' * 1000
        result = normalize_hebrew(long_text)
        assert len(result) == 3000  # 3 consonants * 1000
        assert result == 'אהב' * 1000
    
    def test_special_characters(self):
        """Test handling of special characters."""
        # Should strip non-Hebrew characters
        assert normalize_hebrew('אָב-123-test') == 'אב'
        assert normalize_hebrew('!@#$אהב%^&*') == 'אהב'


class TestIntegration:
    """Integration tests combining multiple functions."""
    
    def test_strongs_to_bhsa_workflow(self):
        """Test typical workflow of comparing Strong's to BHSA."""
        # Simulate Strong's entry
        strongs_entry = {'lemma': 'אָהַב', 'kjv_def': 'love'}
        strongs_normalized = extract_strongs_hebrew(strongs_entry)
        
        # Simulate BHSA data
        bhsa_text = 'אהב'
        
        # Compare
        score = compare_hebrew(strongs_normalized, bhsa_text)
        assert score == 1.0  # Should match perfectly after normalization
    
    def test_spelling_variant_detection(self):
        """Test detection of spelling variants."""
        # Plene vs defective
        text1 = normalize_hebrew('דָּוִד')
        text2 = normalize_hebrew('דָּוִיד')
        
        score = compare_hebrew(text1, text2, fuzzy=True)
        assert score >= 0.7  # Should recognize as similar


# Pytest fixtures
@pytest.fixture
def sample_strongs_entries():
    """Sample Strong's entries for testing."""
    return [
        {'lemma': 'אָב', 'xlit': 'ʼâb', 'kjv_def': 'father'},
        {'lemma': 'אָהַב', 'xlit': 'ʼâhab', 'kjv_def': 'love'},
        {'lemma': 'מֶלֶךְ', 'xlit': 'melek', 'kjv_def': 'king'},
    ]


@pytest.fixture
def sample_hebrew_texts():
    """Sample Hebrew texts for testing."""
    return [
        'אָב',
        'אָהַב',
        'מֶלֶךְ',
        'דָּוִד',
        'יְרוּשָׁלַיִם',
    ]


def test_with_sample_data(sample_strongs_entries, sample_hebrew_texts):
    """Test with sample data fixtures."""
    for entry in sample_strongs_entries:
        normalized = extract_strongs_hebrew(entry)
        assert len(normalized) > 0
        assert is_hebrew_text(normalized)
    
    for text in sample_hebrew_texts:
        normalized = normalize_hebrew(text)
        assert len(normalized) > 0
        stats = get_hebrew_stats(text)
        assert stats['consonants'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
