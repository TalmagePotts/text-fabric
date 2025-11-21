#!/usr/bin/env python3
"""
Quick test for the specific query that failed.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tf.browser.ai_query import search_lexemes, extract_keywords

# Test the query that failed
user_query = "find all mentions of the verb to create followed by the direct object marker"

print("Testing query:", user_query)
print("\n" + "="*60)

# Extract keywords
keywords = extract_keywords(user_query)
print(f"\nExtracted keywords: {keywords}")

# Search for lexemes
print("\nSearching for lexemes:")
for keyword in keywords:
    results = search_lexemes(keyword, max_results=3)
    if results:
        print(f"\n  '{keyword}':")
        for r in results:
            print(f"    - {r['gloss']}: lex={r['lex']} (sp={r['sp']})")

print("\n" + "="*60)
print("\nExpected query should be something like:")
print("""
clause
  v:word lex=BR>[ sp=verb
  o:word lex=>T
  v :> o
""")

print("\nNote: BR>[ = create (verb), >T = direct object marker")
