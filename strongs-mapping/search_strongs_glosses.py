#!/usr/bin/env python3
"""
Search Strong's Glosses in Text-Fabric

This script demonstrates how to search for English words in the Strong's glosses
feature, which contains ALL KJV glosses (not just the primary BHSA gloss).

Usage:
    python3 search_strongs_glosses.py mercy
    python3 search_strongs_glosses.py love
"""

import sys
from pathlib import Path

def search_strongs_glosses(search_term):
    """Search for a term in Strong's glosses using Text-Fabric."""
    
    print(f"Searching for '{search_term}' in Strong's glosses...")
    print("=" * 70)
    
    # Read the strongs_glosses.tf file directly
    tf_file = Path.home() / "text-fabric-data/github/TalmagePotts/strongs/tf/1.0/strongs_glosses.tf"
    strongs_file = Path.home() / "text-fabric-data/github/TalmagePotts/strongs/tf/1.0/strongs.tf"
    
    if not tf_file.exists():
        print(f"✗ Strong's glosses feature not found at: {tf_file}")
        print("\nTo generate it, run:")
        print("  cd strongs-mapping/scripts")
        print("  python3 generate_tf_features.py")
        return
    
    # Load the data
    glosses = {}
    strongs_nums = {}
    
    # Read strongs_glosses.tf
    with open(tf_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('@'):
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    node = int(parts[0])
                    gloss_text = parts[1]
                    glosses[node] = gloss_text
    
    # Read strongs.tf
    with open(strongs_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('@'):
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    node = int(parts[0])
                    strongs_num = parts[1]
                    strongs_nums[node] = strongs_num
    
    print(f"Loaded {len(glosses)} lexemes with Strong's glosses\n")
    
    # Search for the term
    search_lower = search_term.lower()
    matches = []
    
    for node, gloss_text in glosses.items():
        if search_lower in gloss_text.lower():
            strongs_num = strongs_nums.get(node, "???")
            matches.append({
                'node': node,
                'strongs': strongs_num,
                'glosses': gloss_text
            })
    
    # Display results
    if not matches:
        print(f"No matches found for '{search_term}'")
        return
    
    print(f"Found {len(matches)} lexeme(s) with '{search_term}' in Strong's glosses:\n")
    
    for i, match in enumerate(matches, 1):
        print(f"{i}. Node {match['node']} - {match['strongs']}")
        print(f"   Glosses: {match['glosses']}")
        print()
    
    print("=" * 70)
    print("\nTo use these in Text-Fabric queries:")
    print(f"  # Search by Strong's number:")
    for match in matches[:3]:  # Show first 3 examples
        print(f"  word strongs={match['strongs']}")
    
    print(f"\n  # Or search the strongs_glosses feature directly:")
    print(f"  word strongs_glosses~{search_term}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search_strongs_glosses.py <search_term>")
        print("\nExamples:")
        print("  python3 search_strongs_glosses.py mercy")
        print("  python3 search_strongs_glosses.py love")
        print("  python3 search_strongs_glosses.py compassion")
        sys.exit(1)
    
    search_term = sys.argv[1]
    search_strongs_glosses(search_term)


if __name__ == '__main__':
    main()
