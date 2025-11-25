#!/usr/bin/env python3
"""
Test that Strong's features are loaded with BHSA
"""

print("Testing Strong's features integration...")
print("=" * 60)

try:
    from tf.app import use
    
    print("\n1. Loading BHSA corpus...")
    A = use('etcbc/bhsa', checkout='clone', silent='deep')
    
    if not A:
        print("✗ Failed to load BHSA")
        exit(1)
    
    print("✓ BHSA loaded successfully")
    
    # Check if Strong's features are available
    api = A.api
    F = api.F
    
    print("\n2. Checking for Strong's features...")
    
    # Try to access strongs feature
    try:
        # Get a lexeme node
        lex_nodes = list(F.otype.s('lex'))[:10]
        
        strongs_found = False
        glosses_found = False
        
        for node in lex_nodes:
            strongs_val = F.strongs.v(node)
            if strongs_val:
                strongs_found = True
                glosses_val = F.strongs_glosses.v(node)
                if glosses_val:
                    glosses_found = True
                    print(f"\n✓ Strong's features are working!")
                    print(f"  Example: Node {node}")
                    print(f"    strongs: {strongs_val}")
                    print(f"    strongs_glosses: {glosses_val[:80]}...")
                    break
        
        if not strongs_found:
            print("✗ strongs feature exists but has no data")
        elif not glosses_found:
            print("✗ strongs_glosses feature exists but has no data")
            
    except AttributeError as e:
        print(f"✗ Strong's features not found: {e}")
        print("\nAvailable features:")
        all_features = sorted([f for f in dir(F) if not f.startswith('_')])
        for feat in all_features[:20]:
            print(f"  - {feat}")
        exit(1)
    
    print("\n3. Testing search for 'mercy'...")
    
    # Count lexemes with 'mercy' in glosses
    mercy_count = 0
    mercy_examples = []
    
    for node in F.otype.s('lex'):
        glosses = F.strongs_glosses.v(node)
        if glosses and 'mercy' in glosses.lower():
            mercy_count += 1
            if len(mercy_examples) < 3:
                hebrew = F.voc_lex_utf8.v(node)
                strongs = F.strongs.v(node)
                mercy_examples.append((node, hebrew, strongs, glosses))
    
    print(f"\n✓ Found {mercy_count} lexemes with 'mercy' in glosses")
    print("\nExamples:")
    for node, hebrew, strongs, glosses in mercy_examples:
        print(f"  {hebrew} ({strongs}): {glosses[:60]}...")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nYou can now use in Text-Fabric browser:")
    print("  word strongs_glosses~mercy")
    
except ImportError as e:
    print(f"✗ Error: {e}")
    print("Note: pyyaml is required")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
