"""
Create Complete BHSA to Strong's Mapping

Ensures EVERY BHSA lexeme has a Strong's number assigned.
Uses aggressive fuzzy matching for unmatched lexemes.
"""

import json
import sys
sys.path.insert(0, '.')
from hebrew_normalizer import normalize_hebrew, compare_hebrew
import os

def create_complete_bhsa_to_strongs():
    """Create complete BHSA → Strong's mapping with 100% coverage."""
    
    print("Creating Complete BHSA → Strong's Mapping")
    print("=" * 60)
    
    # Load existing Strong's → BHSA mapping
    with open('strongs_to_bhsa.json') as f:
        strongs_mapping = json.load(f)
    
    # Build reverse mapping
    print("\n1. Building reverse mapping from existing matches...")
    bhsa_to_strongs = {}
    
    for strongs_num, entry in strongs_mapping.items():
        for match in entry['bhsa_matches']:
            bhsa_voc = match['bhsa_voc']
            bhsa_cons = match['bhsa_lex']
            
            # Store by vocalized form (primary key)
            if bhsa_voc and bhsa_voc not in bhsa_to_strongs:
                bhsa_to_strongs[bhsa_voc] = {
                    'strongs': strongs_num,
                    'strongs_lemma': entry['strongs_lemma'],
                    'score': match['score'],
                    'method': 'exact_match',
                    'kjv_glosses': entry['kjv_glosses']
                }
    
    print(f"   ✓ {len(bhsa_to_strongs)} BHSA lexemes matched")
    
    # Load all BHSA lexemes
    print("\n2. Loading all BHSA lexemes...")
    bhsa_path = '/home/teapot/text-fabric-data/github/ETCBC/bhsa/tf/2021'
    
    with open(os.path.join(bhsa_path, 'lex_utf8.tf'), 'r', encoding='utf-8') as f:
        lex_lines = [l.strip() for l in f if l.strip() and not l.startswith('@')]
    
    with open(os.path.join(bhsa_path, 'voc_lex_utf8.tf'), 'r', encoding='utf-8') as f:
        voc_lex_lines = [l.strip() for l in f if l.strip() and not l.startswith('@')]
    
    # Get unique lexemes
    all_bhsa = {}
    for i in range(min(len(lex_lines), 426590)):
        voc_lex = voc_lex_lines[i] if i < len(voc_lex_lines) else ''
        lex = lex_lines[i]
        
        if voc_lex and voc_lex not in all_bhsa:
            all_bhsa[voc_lex] = {
                'voc': voc_lex,
                'cons': lex,
                'normalized': normalize_hebrew(voc_lex)
            }
    
    print(f"   ✓ {len(all_bhsa)} unique BHSA lexemes found")
    
    # Find unmatched
    unmatched = [lex for lex in all_bhsa.keys() if lex not in bhsa_to_strongs]
    print(f"   ✓ {len(unmatched)} unmatched BHSA lexemes")
    
    # Get all Strong's entries for fuzzy matching
    print("\n3. Applying fuzzy matching to unmatched lexemes...")
    all_strongs = {
        num: {
            'lemma': entry['strongs_lemma'],
            'normalized': entry['strongs_normalized'],
            'glosses': entry['kjv_glosses']
        }
        for num, entry in strongs_mapping.items()
    }
    
    matched_count = 0
    for bhsa_lex in unmatched:
        bhsa_data = all_bhsa[bhsa_lex]
        best_match = None
        best_score = 0
        
        # Try to find best match
        for strongs_num, strongs_data in all_strongs.items():
            score = compare_hebrew(bhsa_data['normalized'], strongs_data['normalized'])
            
            if score > best_score:
                best_score = score
                best_match = {
                    'strongs': strongs_num,
                    'strongs_lemma': strongs_data['lemma'],
                    'score': round(score, 3),
                    'method': 'fuzzy_match' if score < 0.9 else 'consonantal_match',
                    'kjv_glosses': strongs_data['glosses']
                }
        
        # Assign best match (even if score is low)
        if best_match:
            bhsa_to_strongs[bhsa_lex] = best_match
            matched_count += 1
            
            if matched_count % 100 == 0:
                print(f"   Progress: {matched_count}/{len(unmatched)} ({100*matched_count/len(unmatched):.1f}%)")
    
    print(f"   ✓ Matched {matched_count} additional lexemes")
    
    # Calculate statistics
    print("\n4. Generating statistics...")
    total = len(all_bhsa)
    exact = sum(1 for v in bhsa_to_strongs.values() if v['method'] == 'exact_match')
    consonantal = sum(1 for v in bhsa_to_strongs.values() if v['method'] == 'consonantal_match')
    fuzzy = sum(1 for v in bhsa_to_strongs.values() if v['method'] == 'fuzzy_match')
    high_conf = sum(1 for v in bhsa_to_strongs.values() if v['score'] >= 0.9)
    medium_conf = sum(1 for v in bhsa_to_strongs.values() if 0.7 <= v['score'] < 0.9)
    low_conf = sum(1 for v in bhsa_to_strongs.values() if v['score'] < 0.7)
    
    # Save complete mapping
    print("\n5. Saving complete mapping...")
    with open('bhsa_to_strongs_complete.json', 'w', encoding='utf-8') as f:
        json.dump(bhsa_to_strongs, f, ensure_ascii=False, indent=2)
    
    print(f"   ✓ Saved to bhsa_to_strongs_complete.json")
    
    # Create summary
    summary = {
        'total_bhsa_lexemes': total,
        'total_matched': len(bhsa_to_strongs),
        'coverage': round(100 * len(bhsa_to_strongs) / total, 2),
        'by_method': {
            'exact_match': exact,
            'consonantal_match': consonantal,
            'fuzzy_match': fuzzy
        },
        'by_confidence': {
            'high (≥0.9)': high_conf,
            'medium (0.7-0.89)': medium_conf,
            'low (<0.7)': low_conf
        }
    }
    
    with open('bhsa_to_strongs_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("COMPLETE BHSA → STRONG'S MAPPING SUMMARY")
    print("=" * 60)
    print(f"Total BHSA lexemes: {total}")
    print(f"Total matched: {len(bhsa_to_strongs)} ({summary['coverage']}%)")
    print()
    print("By Method:")
    print(f"  Exact match: {exact}")
    print(f"  Consonantal match: {consonantal}")
    print(f"  Fuzzy match: {fuzzy}")
    print()
    print("By Confidence:")
    print(f"  High (≥0.9): {high_conf}")
    print(f"  Medium (0.7-0.89): {medium_conf}")
    print(f"  Low (<0.7): {low_conf}")
    print()
    
    if summary['coverage'] == 100.0:
        print("✓ 100% COVERAGE ACHIEVED!")
    
    print("=" * 60)
    
    # Show sample low-confidence matches
    print("\nSample low-confidence matches (for review):")
    low_conf_samples = [(k, v) for k, v in bhsa_to_strongs.items() if v['score'] < 0.7]
    for i, (bhsa, match) in enumerate(low_conf_samples[:10], 1):
        print(f"{i:2}. {bhsa:20} → {match['strongs']} {match['strongs_lemma']:15} (score: {match['score']})")
    
    return bhsa_to_strongs, summary

if __name__ == '__main__':
    mapping, summary = create_complete_bhsa_to_strongs()
