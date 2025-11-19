#!/usr/bin/env python3
"""
Test script for English translation integration.

This script tests the English translation functionality by:
1. Loading the BHSA corpus
2. Running a simple query
3. Displaying results with English translations
"""

import sys
import os

# Add the tf module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tf'))

from tf.app import use

def test_english_translation():
    """Test English translation display."""
    
    print("Loading BHSA corpus...")
    A = use('etcbc/bhsa', checkout="clone")
    
    if not A:
        print("Failed to load BHSA corpus")
        return False
    
    print("? Corpus loaded successfully\n")
    
    # Test the English translation module directly
    print("Testing English translation module...")
    from tf.advanced.english import get_english_provider
    
    english = get_english_provider()
    
    if not english.enabled:
        print("? English translations not available")
        print("  Make sure translation data files are in English-lineup/")
        print("  Required files:")
        print("    - BHSA-with-interlinear-translation.csv")
        print("    - bhsa_ohb_offsets.json")
        return False
    
    print("? English translation provider initialized\n")
    
    # Test translation for a specific node (Genesis 1:1, first word)
    test_node = 1  # "???" (in)
    trans = english.get_translation(test_node)
    
    if trans:
        print(f"Test translation for node {test_node}:")
        print(f"  Hebrew: (node {test_node})")
        print(f"  Gloss: {trans['gloss']}")
        print(f"  English: {trans['english']}")
        print(f"  BSB sort: {trans['bsb_sort']}")
        print("? Translation lookup working\n")
    else:
        print(f"? No translation found for node {test_node}\n")
    
    # Run a simple query
    print("Running test query: 'word sp=verb' (first 3 results)...")
    query = "word sp=verb"
    
    try:
        results = A.search(query)
        result_list = list(results)[:3]
        
        print(f"? Found {len(result_list)} results (showing first 3)\n")
        
        # Display results with English
        print("Testing display with English translations:")
        print("=" * 60)
        
        for i, nodes in enumerate(result_list, 1):
            # Get the word node
            word_node = nodes[0] if isinstance(nodes, tuple) else nodes
            
            # Get Hebrew text
            hebrew = A.api.F.g_word_utf8.v(word_node)
            
            # Get English translation
            trans = english.get_translation(word_node)
            english_text = trans['english'] if trans and trans['english'] else "(no translation)"
            
            # Get reference
            ref = A.api.T.sectionFromNode(word_node)
            ref_str = f"{ref[0]} {ref[1]}:{ref[2]}"
            
            print(f"{i}. {hebrew} ({english_text}) - {ref_str}")
        
        print("=" * 60)
        print("\n? Display test completed\n")
        
        # Test the actual pretty display with showEnglish option
        print("Testing pretty display with showEnglish=True:")
        print("-" * 60)
        
        # Display first result with English
        A.displaySetup(showEnglish=True)
        A.pretty(result_list[0])
        
        print("-" * 60)
        print("\n? Pretty display test completed\n")
        
        return True
        
    except Exception as e:
        print(f"? Query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("English Translation Integration Test")
    print("=" * 60)
    print()
    
    success = test_english_translation()
    
    print()
    print("=" * 60)
    if success:
        print("? All tests passed!")
        print("\nTo use English translations in the browser:")
        print("1. Start Text-Fabric browser: tf etcbc/bhsa")
        print("2. Go to Options tab")
        print("3. Check 'English translation' checkbox")
        print("4. Run a query and expand results to see translations")
    else:
        print("? Some tests failed")
        print("\nPlease check:")
        print("1. BHSA corpus is installed")
        print("2. Translation data files are in English-lineup/")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
