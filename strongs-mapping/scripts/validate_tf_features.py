"""
Validate Text-Fabric Strong's Features

Tests that the generated TF features load correctly and work with BHSA.
"""

import sys
sys.path.insert(0, '.')

def test_feature_loading():
    """Test that Strong's features load with BHSA."""
    print("=" * 60)
    print("Testing Strong's TF Feature Loading")
    print("=" * 60)
    
    try:
        from tf.app import use
        
        print("\n1. Loading BHSA with Strong's module...")
        A = use('etcbc/bhsa', mod='TalmagePotts/strongs', silent='deep')
        
        if not A:
            print("✗ Failed to load BHSA with Strong's module")
            return False
        
        print("✓ Successfully loaded BHSA with Strong's module")
        
        # Get API
        api = A.api
        F = api.F
        L = api.L
        T = api.T
        
        # Check if features exist
        print("\n2. Checking feature availability...")
        
        if not hasattr(F, 'strongs'):
            print("✗ 'strongs' feature not found")
            return False
        print("✓ 'strongs' feature available")
        
        if not hasattr(F, 'strongs_glosses'):
            print("✗ 'strongs_glosses' feature not found")
            return False
        print("✓ 'strongs_glosses' feature available")
        
        # Test on sample lexemes
        print("\n3. Testing features on sample lexemes...")
        
        lex_nodes = F.otype.s('lex')
        sample_count = 0
        feature_count = 0
        
        for lex_node in list(lex_nodes)[:100]:
            sample_count += 1
            strongs_num = F.strongs.v(lex_node)
            
            if strongs_num:
                feature_count += 1
                glosses = F.strongs_glosses.v(lex_node)
                hebrew = F.voc_lex_utf8.v(lex_node)
                
                if sample_count <= 5:
                    print(f"  {hebrew:15} → {strongs_num:6} ({glosses[:40]}...)")
        
        print(f"\n✓ Tested {sample_count} lexemes, {feature_count} have Strong's features")
        
        # Calculate coverage
        print("\n4. Calculating coverage...")
        
        total_lex = len(list(lex_nodes))
        with_strongs = sum(1 for node in lex_nodes if F.strongs.v(node))
        
        coverage = 100 * with_strongs / total_lex
        
        print(f"  Total lexemes: {total_lex}")
        print(f"  With Strong's: {with_strongs}")
        print(f"  Coverage: {coverage:.1f}%")
        
        if coverage < 70:
            print("⚠ Warning: Coverage is low")
        else:
            print("✓ Coverage is good")
        
        print("\n" + "=" * 60)
        print("✓ All validation tests passed!")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"✗ Error: Text-Fabric not available: {e}")
        print("  Note: This is expected if running without pyyaml")
        return False
    except Exception as e:
        print(f"✗ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_feature_loading()
    sys.exit(0 if success else 1)
