"""
Test script to validate all examples in the production AI prompt template.
"""

from tf.app import use

# Load BHSA corpus
A = use('BHSA', hoist=globals())

print("=" * 80)
print("TESTING PRODUCTION TEMPLATE EXAMPLES")
print("=" * 80)

# Test queries from production template
test_queries = [
    # Basic examples
    ("Basic: All verbs", "word sp=verb"),
    ("Basic: YHWH", "word lex=JHWH/"),
    ("Basic: Plural feminine nouns", "word sp=subs gn=f nu=pl"),
    ("Basic: Perfect qal verbs", "word sp=verb vs=qal vt=perf"),
    
    # Containment examples
    ("Containment: Verbs in Genesis", """book book=Genesis
  word sp=verb"""),
    
    ("Containment: Wayyiqtol in verbal clauses", """clause kind=VC
  word sp=verb vt=wayq"""),
    
    # Relational examples
    ("Relation: Verb before noun", """clause
  vb:word sp=verb
  n:word sp=subs
  vb < n"""),
    
    ("Relation: Verb immediately before noun", """sentence
  v:word sp=verb
  n:word sp=subs
  v :> n"""),
    
    # Quantifier examples
    ("Quantifier: Clauses without verbs", """clause /without/
  word sp=verb
/-/"""),
    
    ("Quantifier: Feminine not plural", """word gn=f /without/
  .. nu=pl
/-/"""),
    
    ("Quantifier: Phrases with all masculine words", """phrase /where/
  word
/have/
  .. gn=m
/-/"""),
    
    ("Quantifier: Clauses with subject OR object", """clause /with/
  phrase function=Subj
/or/
  phrase function=Objc
/-/"""),
    
    # Complex examples
    ("Complex: NTN[ with L after", """clause
  w:word lex=NTN[
  l:word lex=L
  w :> l"""),
]

results = []
for name, query in test_queries:
    try:
        result = A.search(query, silent=True)
        count = len(result) if result else 0
        status = "✅ PASS" if count > 0 else "⚠️  ZERO"
        results.append((name, status, count, None))
        print(f"{status} {name}: {count} results")
    except Exception as e:
        results.append((name, "❌ FAIL", 0, str(e)))
        print(f"❌ FAIL {name}: {str(e)[:100]}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

passed = sum(1 for _, status, _, _ in results if status == "✅ PASS")
zero = sum(1 for _, status, _, _ in results if status == "⚠️  ZERO")
failed = sum(1 for _, status, _, _ in results if status == "❌ FAIL")

print(f"Passed: {passed}/{len(results)}")
print(f"Zero results (valid but empty): {zero}/{len(results)}")
print(f"Failed (syntax error): {failed}/{len(results)}")

if failed > 0:
    print("\n" + "=" * 80)
    print("FAILED QUERIES")
    print("=" * 80)
    for name, status, count, error in results:
        if status == "❌ FAIL":
            print(f"\n{name}:")
            print(f"  Error: {error}")

print("\n" + "=" * 80)
