"""
Create Supplementary Mapping for Unmatched BHSA Lexemes

This script creates a reverse mapping (BHSA → Strong's) and identifies
unmatched BHSA lexemes, then attempts to find Strong's matches using
relaxed matching criteria.
"""

import json
import os
import sys
sys.path.insert(0, '.')
from hebrew_normalizer import normalize_hebrew, compare_hebrew

def create_bhsa_to_strongs_mapping():
    """Create reverse mapping from BHSA to Strong's."""
    print("Creating BHSA → Strong's reverse mapping...")
    
    with open('strongs_to_bhsa.json') as f:
        strongs_mapping = json.load(f)
    
    # Build reverse index
    bhsa_to_strongs = {}
    
    for strongs_num, entry in strongs_mapping.items():
        for match in entry['bhsa_matches']:
            bhsa_lex = match['bhsa_lex']
            bhsa_voc = match['bhsa_voc']
            
            # Index by both consonantal and vocalized
            for key in [bhsa_lex, bhsa_voc]:
                if key and key not in bhsa_to_strongs:
                    bhsa_to_strongs[key] = []
                if key:
                    bhsa_to_strongs[key].append({
                        'strongs': strongs_num,
                        'strongs_lemma': entry['strongs_lemma'],
                        'score': match['score'],
                        'kjv_glosses': entry['kjv_glosses']
                    })
    
    print(f"✓ Created reverse mapping for {len(bhsa_to_strongs)} BHSA lexemes")
    return bhsa_to_strongs


def find_unmatched_bhsa():
    """Find BHSA lexemes without Strong's matches."""
    print("\nFinding unmatched BHSA lexemes...")
    
    # Load BHSA data
    bhsa_path = '/home/teapot/text-fabric-data/github/ETCBC/bhsa/tf/2021'
    
    with open(os.path.join(bhsa_path, 'lex_utf8.tf'), 'r', encoding='utf-8') as f:
        lex_lines = [l.strip() for l in f if l.strip() and not l.startswith('@')]
    
    with open(os.path.join(bhsa_path, 'voc_lex_utf8.tf'), 'r', encoding='utf-8') as f:
        voc_lex_lines = [l.strip() for l in f if l.strip() and not l.startswith('@')]
    
    # Get unique lexemes
    unique_lexemes = {}
    for i in range(min(len(lex_lines), 426590)):
        lex = lex_lines[i]
        voc_lex = voc_lex_lines[i] if i < len(voc_lex_lines) else ''
        
        if voc_lex:
            key = voc_lex
            if key not in unique_lexemes:
                unique_lexemes[key] = {
                    'voc': voc_lex,
                    'cons': lex,
                    'normalized': normalize_hebrew(voc_lex)
                }
    
    print(f"✓ Found {len(unique_lexemes)} unique BHSA lexemes")
    return unique_lexemes


def find_supplementary_matches():
    """Find matches for previously unmatched BHSA lexemes."""
    print("\nFinding supplementary matches...")
    
    # Load existing mapping
    bhsa_to_strongs = create_bhsa_to_strongs_mapping()
    all_bhsa = find_unmatched_bhsa()
    
    # Load unmatched Strong's entries
    with open('strongs_to_bhsa.json') as f:
        strongs_mapping = json.load(f)
    
    unmatched_strongs = {
        num: entry for num, entry in strongs_mapping.items()
        if entry['match_count'] == 0
    }
    
    print(f"  Unmatched Strong's entries: {len(unmatched_strongs)}")
    
    # Find unmatched BHSA
    unmatched_bhsa = {
        key: data for key, data in all_bhsa.items()
        if key not in bhsa_to_strongs and data['cons'] not in bhsa_to_strongs
    }
    
    print(f"  Unmatched BHSA lexemes: {len(unmatched_bhsa)}")
    
    # Try to match using relaxed criteria
    supplementary_matches = {}
    
    for bhsa_key, bhsa_data in list(unmatched_bhsa.items())[:100]:  # Limit to first 100
        best_match = None
        best_score = 0
        
        for strongs_num, strongs_entry in unmatched_strongs.items():
            # Compare normalized forms
            score = compare_hebrew(bhsa_data['normalized'], strongs_entry['strongs_normalized'])
            
            if score > best_score and score >= 0.6:  # Lower threshold
                best_score = score
                best_match = {
                    'strongs': strongs_num,
                    'strongs_lemma': strongs_entry['strongs_lemma'],
                    'score': round(score, 3),
                    'kjv_glosses': strongs_entry['kjv_glosses']
                }
        
        if best_match:
            supplementary_matches[bhsa_key] = best_match
    
    print(f"✓ Found {len(supplementary_matches)} supplementary matches")
    
    # Save results
    output = {
        'total_bhsa_lexemes': len(all_bhsa),
        'matched_in_main_mapping': len(bhsa_to_strongs),
        'unmatched': len(unmatched_bhsa),
        'supplementary_matches': supplementary_matches,
        'unmatched_bhsa_sample': {
            k: v for k, v in list(unmatched_bhsa.items())[:40]
        }
    }
    
    with open('bhsa_supplementary_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Saved to bhsa_supplementary_mapping.json")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUPPLEMENTARY MAPPING SUMMARY")
    print("=" * 60)
    print(f"Total BHSA lexemes: {len(all_bhsa)}")
    print(f"Matched in main mapping: {len(bhsa_to_strongs)} ({100*len(bhsa_to_strongs)/len(all_bhsa):.1f}%)")
    print(f"Unmatched: {len(unmatched_bhsa)} ({100*len(unmatched_bhsa)/len(all_bhsa):.1f}%)")
    print(f"New supplementary matches: {len(supplementary_matches)}")
    print()
    
    if supplementary_matches:
        print("Sample supplementary matches:")
        for i, (bhsa, match) in enumerate(list(supplementary_matches.items())[:10], 1):
            print(f"{i:2}. {bhsa:15} → {match['strongs']} {match['strongs_lemma']} (score: {match['score']})")
    
    return output


if __name__ == '__main__':
    result = find_supplementary_matches()
