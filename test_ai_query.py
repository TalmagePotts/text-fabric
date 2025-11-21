#!/usr/bin/env python3
"""
Test script for AI query generation module.
This script tests the lexeme lookup and query validation without requiring API calls.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tf.browser.ai_query import (
    load_lexemes,
    search_lexemes,
    extract_keywords,
    validate_query,
    build_system_prompt
)

def test_lexeme_loading():
    """Test that lexemes load correctly."""
    print("Testing lexeme loading...")
    try:
        df = load_lexemes()
        print(f"✅ Loaded {len(df)} lexemes")
        print(f"   Sample: {df.head(3)[['lex', 'sp', 'gloss']].to_dict('records')}")
        return True
    except Exception as e:
        print(f"❌ Error loading lexemes: {e}")
        return False

def test_lexeme_search():
    """Test lexeme search functionality."""
    print("\nTesting lexeme search...")
    test_cases = [
        ("give", "NTN["),
        ("YHWH", "JHWH/"),
        ("create", "BR>["),
        ("God", ">LHJM/"),
    ]
    
    all_passed = True
    for search_term, expected_lex in test_cases:
        results = search_lexemes(search_term, max_results=5)
        if results:
            found = any(r['lex'] == expected_lex for r in results)
            status = "✅" if found else "⚠️"
            print(f"   {status} '{search_term}' -> {results[0]['lex']} (expected {expected_lex})")
            if not found:
                print(f"      Found: {[r['lex'] for r in results]}")
        else:
            print(f"   ❌ '{search_term}' -> No results")
            all_passed = False
    
    return all_passed

def test_keyword_extraction():
    """Test keyword extraction from user prompts."""
    print("\nTesting keyword extraction...")
    test_prompts = [
        "Search for all the times the verb which means to give has the preposition Lamed right after it",
        "Find the divine name YHWH",
        "Find all verbs in Genesis",
    ]
    
    for prompt in test_prompts:
        keywords = extract_keywords(prompt)
        print(f"   '{prompt[:50]}...'")
        print(f"      Keywords: {keywords}")
    
    return True

def test_query_validation():
    """Test query validation."""
    print("\nTesting query validation...")
    
    valid_queries = [
        "word sp=verb",
        "word lex=JHWH/",
        "clause\n  w:word lex=NTN[\n  l:word lex=L\n  l :> w",
    ]
    
    invalid_queries = [
        "word pos=verb",  # Should be sp=
        "word gender=m",  # Should be gn=
        "\tword sp=verb",  # Tab instead of spaces
        "word sp=verb\n word sp=subs",  # Odd indentation
    ]
    
    print("   Valid queries:")
    for query in valid_queries:
        is_valid, error = validate_query(query)
        status = "✅" if is_valid else "❌"
        print(f"      {status} {query.split(chr(10))[0][:40]}")
        if error:
            print(f"         Error: {error}")
    
    print("   Invalid queries (should fail):")
    for query in invalid_queries:
        is_valid, error = validate_query(query)
        status = "✅" if not is_valid else "❌"
        print(f"      {status} {query.split(chr(10))[0][:40]}")
        if error:
            print(f"         Error: {error}")
    
    return True

def test_system_prompt():
    """Test system prompt generation."""
    print("\nTesting system prompt generation...")
    prompt = build_system_prompt()
    
    # Check for key components
    checks = [
        ("CRITICAL RULES" in prompt, "Contains critical rules"),
        ("CORE FEATURES" in prompt, "Contains feature reference"),
        ("VERIFIED EXAMPLES" in prompt, "Contains examples"),
        ("word sp=verb" in prompt, "Contains basic example"),
        ("lex=NTN[" in prompt, "Contains lexeme example"),
    ]
    
    all_passed = True
    for passed, description in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {description}")
        if not passed:
            all_passed = False
    
    print(f"   Prompt length: {len(prompt)} characters")
    return all_passed

def main():
    """Run all tests."""
    print("=" * 60)
    print("AI Query Generation Module Tests")
    print("=" * 60)
    
    tests = [
        test_lexeme_loading,
        test_lexeme_search,
        test_keyword_extraction,
        test_query_validation,
        test_system_prompt,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
