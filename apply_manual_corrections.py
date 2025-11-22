"""
Manual Corrections for Low-Confidence BHSA to Strong's Mappings

This file contains manual corrections for common particles and words
that didn't match well with fuzzy matching.
"""

# Manual corrections for common Hebrew particles and prepositions
MANUAL_CORRECTIONS = {
    # Prepositions
    'בְּ': 'H9003',      # bet prefix - in, with, by
    'לְ': 'H9005',       # lamed prefix - to, for
    'כְּ': 'H9004',      # kaph prefix - like, as
    'מִ': 'H4480',       # min - from
    'מִן': 'H4480',      # min - from
    
    # Definite article
    'הַ': 'H9009',       # ha prefix - the
    'הָ': 'H9009',       # ha prefix - the
    
    # Conjunctions
    'וְ': 'H9002',       # vav prefix - and
    'וַ': 'H9002',       # vav prefix - and
    'וָ': 'H9002',       # vav prefix - and
    
    # Direct object marker
    'אֵת': 'H853',       # et - direct object marker
    'אֶת': 'H853',       # et - direct object marker
    
    # Common words that may have been mismatched
    'לַיְלָה': 'H3915',  # laylah - night
    'יוֹם': 'H3117',     # yom - day
    'שָׁנָה': 'H8141',   # shanah - year
    'עִיר': 'H5892',     # ir - city
    'בַּיִת': 'H1004',   # bayit - house
    'אִישׁ': 'H376',     # ish - man
    'אִשָּׁה': 'H802',   # ishah - woman
    'בֵּן': 'H1121',     # ben - son
    'בַּת': 'H1323',     # bat - daughter
    'מֶלֶךְ': 'H4428',   # melekh - king
    'עַם': 'H5971',      # am - people
    'גּוֹי': 'H1471',    # goy - nation
    'אֶרֶץ': 'H776',     # eretz - land, earth
    'שָׁמַיִם': 'H8064', # shamayim - heaven, sky
    'מַיִם': 'H4325',    # mayim - water
    'יָד': 'H3027',      # yad - hand
    'עַיִן': 'H5869',    # ayin - eye
    'לֵב': 'H3820',      # lev - heart
    'נֶפֶשׁ': 'H5315',   # nefesh - soul, life
    'רוּחַ': 'H7307',    # ruach - spirit, wind
    'דָּבָר': 'H1697',   # davar - word, thing
    'דֶּרֶךְ': 'H1870',  # derekh - way, road
    'עֵת': 'H6256',      # et - time
    'מָקוֹם': 'H4725',   # makom - place
    'שֵׁם': 'H8034',     # shem - name
    'קוֹל': 'H6963',     # kol - voice, sound
    'פֶּה': 'H6310',     # peh - mouth
    'אֹזֶן': 'H241',     # ozen - ear
    'רֹאשׁ': 'H7218',    # rosh - head
    'רֶגֶל': 'H7272',    # regel - foot
}

def apply_manual_corrections():
    """Apply manual corrections to the BHSA to Strong's mapping."""
    import json
    
    # Load the complete mapping
    with open('bhsa_to_strongs_complete.json', 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    # Load Strong's data for reference
    with open('strongs_to_bhsa.json', 'r', encoding='utf-8') as f:
        strongs_data = json.load(f)
    
    corrections_made = 0
    
    for bhsa_word, correct_strongs in MANUAL_CORRECTIONS.items():
        if bhsa_word in mapping:
            old_match = mapping[bhsa_word]
            
            # Get Strong's data
            if correct_strongs in strongs_data:
                strongs_entry = strongs_data[correct_strongs]
                
                # Update mapping
                mapping[bhsa_word] = {
                    'strongs': correct_strongs,
                    'strongs_lemma': strongs_entry['strongs_lemma'],
                    'score': 1.0,  # Manual correction = perfect score
                    'method': 'manual_correction',
                    'kjv_glosses': strongs_entry['kjv_glosses'],
                    'previous_match': old_match['strongs']  # Keep track of what it was
                }
                
                corrections_made += 1
                print(f"✓ Corrected {bhsa_word}: {old_match['strongs']} → {correct_strongs}")
    
    # Save corrected mapping
    with open('bhsa_to_strongs_complete.json', 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Applied {corrections_made} manual corrections")
    
    # Update statistics
    exact = sum(1 for v in mapping.values() if v['method'] in ['exact_match', 'manual_correction'])
    consonantal = sum(1 for v in mapping.values() if v['method'] == 'consonantal_match')
    fuzzy = sum(1 for v in mapping.values() if v['method'] == 'fuzzy_match')
    high_conf = sum(1 for v in mapping.values() if v['score'] >= 0.9)
    medium_conf = sum(1 for v in mapping.values() if 0.7 <= v['score'] < 0.9)
    low_conf = sum(1 for v in mapping.values() if v['score'] < 0.7)
    
    summary = {
        'total_bhsa_lexemes': len(mapping),
        'total_matched': len(mapping),
        'coverage': 100.0,
        'by_method': {
            'exact_match': exact - corrections_made,
            'manual_correction': corrections_made,
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
    
    print("\nUpdated Statistics:")
    print(f"  Manual corrections: {corrections_made}")
    print(f"  High confidence: {high_conf}")
    print(f"  Medium confidence: {medium_conf}")
    print(f"  Low confidence: {low_conf}")
    
    return mapping, summary

if __name__ == '__main__':
    mapping, summary = apply_manual_corrections()
