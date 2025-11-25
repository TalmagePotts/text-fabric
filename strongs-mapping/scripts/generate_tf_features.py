"""
Generate Text-Fabric Features from Strong's Mapping

Creates two TF features for BHSA lexeme nodes:
1. 'strongs' - Strong's Concordance number (e.g., "H157")
2. 'strongs_glosses' - KJV English glosses (comma-separated)

Usage:
    python generate_tf_features.py

Output:
    ~/text-fabric-data/github/TalmagePotts/strongs/tf/1.0/
        ├── strongs.tf
        ├── strongs_glosses.tf
        └── otext.tf
"""

import json
import os
from pathlib import Path

def load_mappings():
    """Load the Strong's to BHSA mapping."""
    print("Loading mappings...")
    
    # Get script directory and navigate to data
    script_dir = Path(__file__).parent
    mapping_file = script_dir.parent / 'data/strongs_to_bhsa.json'
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        strongs_mapping = json.load(f)
    
    print(f"✓ Loaded {len(strongs_mapping)} Strong's entries")
    return strongs_mapping


def create_feature_dicts(strongs_mapping, min_score=0.9):
    """
    Create feature dictionaries for TF.
    
    Args:
        strongs_mapping: Strong's to BHSA mapping data
        min_score: Minimum match score to include (default: 0.9)
    
    Returns:
        Tuple of (strongs_dict, glosses_dict)
    """
    print(f"\nCreating feature dictionaries (min_score={min_score})...")
    
    # First pass: collect all Strong's numbers and glosses per node
    node_data = {}  # node -> list of (strongs_num, glosses)
    
    total_matches = 0
    high_conf_matches = 0
    
    for strongs_num, entry in strongs_mapping.items():
        for match in entry['bhsa_matches']:
            if match['score'] >= min_score:
                node = match['node']
                
                if node not in node_data:
                    node_data[node] = []
                
                node_data[node].append({
                    'strongs': strongs_num,
                    'glosses': entry['kjv_glosses']
                })
                
                high_conf_matches += 1
            
            total_matches += 1
    
    # Second pass: combine data for nodes with multiple Strong's numbers
    strongs_dict = {}
    glosses_dict = {}
    multi_strongs_count = 0
    
    for node, entries in node_data.items():
        if len(entries) == 1:
            # Single Strong's number for this node
            strongs_dict[node] = entries[0]['strongs']
            glosses_dict[node] = entries[0]['glosses']
        else:
            # Multiple Strong's numbers - combine them
            multi_strongs_count += 1
            # Use the first Strong's number (or could use semicolon-separated list)
            strongs_dict[node] = entries[0]['strongs']
            
            # Combine all unique glosses
            all_glosses = set()
            for entry in entries:
                # Split glosses and add to set
                glosses = [g.strip() for g in entry['glosses'].split(',')]
                all_glosses.update(glosses)
            
            # Sort and join
            glosses_dict[node] = ','.join(sorted(all_glosses))
    
    print(f"✓ Created features for {len(strongs_dict)} lexeme nodes")
    print(f"  Total matches: {total_matches}")
    print(f"  High confidence (≥{min_score}): {high_conf_matches}")
    print(f"  Nodes with multiple Strong's numbers: {multi_strongs_count}")
    print(f"  Coverage: {100*high_conf_matches/total_matches:.1f}%")
    
    return strongs_dict, glosses_dict


def write_tf_features(strongs_dict, glosses_dict, output_dir):
    """
    Write TF feature files manually (without TF API dependency).
    
    Args:
        strongs_dict: Node → Strong's number mapping
        glosses_dict: Node → glosses mapping
        output_dir: Output directory path
    """
    print(f"\nWriting TF features to {output_dir}...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write strongs.tf
    strongs_file = output_path / 'strongs.tf'
    with open(strongs_file, 'w', encoding='utf-8') as f:
        # Write metadata
        f.write("@node\n")
        f.write("@author=Talmage Potts\n")
        f.write("@dataset=strongs\n")
        f.write("@datasetName=Strong's Concordance Integration for BHSA\n")
        f.write("@description=Strong's Concordance number for Hebrew lexemes\n")
        f.write("@source=OpenScriptures Strong's Hebrew Concordance\n")
        f.write("@valueType=str\n")
        f.write("@version=1.0\n")
        f.write("@writtenBy=generate_tf_features.py\n")
        f.write("@dateWritten=2025-11-21\n")
        f.write("\n")
        
        # Write data (sorted by node number)
        for node in sorted(strongs_dict.keys()):
            f.write(f"{node}\t{strongs_dict[node]}\n")
    
    print(f"✓ Created {strongs_file}")
    
    # Write strongs_glosses.tf
    glosses_file = output_path / 'strongs_glosses.tf'
    with open(glosses_file, 'w', encoding='utf-8') as f:
        # Write metadata
        f.write("@node\n")
        f.write("@author=Talmage Potts\n")
        f.write("@dataset=strongs\n")
        f.write("@datasetName=Strong's Concordance Integration for BHSA\n")
        f.write("@description=KJV English glosses from Strong's Concordance (comma-separated)\n")
        f.write("@source=OpenScriptures Strong's Hebrew Concordance\n")
        f.write("@valueType=str\n")
        f.write("@version=1.0\n")
        f.write("@writtenBy=generate_tf_features.py\n")
        f.write("@dateWritten=2025-11-21\n")
        f.write("\n")
        
        # Write data (sorted by node number)
        for node in sorted(glosses_dict.keys()):
            f.write(f"{node}\t{glosses_dict[node]}\n")
    
    print(f"✓ Created {glosses_file}")
    
    # Write otext.tf (metadata)
    otext_file = output_path / 'otext.tf'
    with open(otext_file, 'w', encoding='utf-8') as f:
        f.write("@config\n")
        f.write("@author=Talmage Potts\n")
        f.write("@dataset=strongs\n")
        f.write("@datasetName=Strong's Concordance Integration for BHSA\n")
        f.write("@version=1.0\n")
        f.write("@fmt:text-orig-full={voc_lex_utf8}\n")
        f.write("@fmt:lex-orig-full={lex_utf8} {strongs}\n")
        f.write("@sectionFeatures=book,chapter,verse\n")
        f.write("@sectionTypes=book,chapter,verse\n")
        f.write("@structureFeatures=book,chapter,verse\n")
        f.write("@structureTypes=book,chapter,verse\n")
        f.write("@textFeatures=voc_lex_utf8,lex_utf8,strongs,strongs_glosses\n")
    
    print(f"✓ Created {otext_file}")


def create_config_yaml(output_dir):
    """Create config.yaml for the TF module."""
    config_path = Path(output_dir).parent.parent / 'config.yaml'
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write("""provenanceSpec:
  org: TalmagePotts
  repo: strongs
  version: 1.0
  doi: ""
  
featureSpecs:
  strongs:
    description: "Strong's Concordance number for Hebrew lexemes"
    valueType: "str"
    
  strongs_glosses:
    description: "KJV English glosses from Strong's Concordance"
    valueType: "str"
""")
    
    print(f"✓ Created {config_path}")


def create_readme(output_dir):
    """Create README for the TF module."""
    readme_path = Path(output_dir).parent.parent / 'README.md'
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("""# Strong's Concordance Integration for BHSA

Text-Fabric module providing Strong's Concordance numbers and KJV glosses for BHSA Hebrew lexemes.

## Features

- **strongs**: Strong's Concordance number (e.g., "H157" for אָהַב "love")
- **strongs_glosses**: KJV English translations (comma-separated)

## Installation

This module is automatically available when using Text-Fabric with BHSA.

## Usage

```python
from tf.app import use

# Load BHSA with Strong's features
A = use('etcbc/bhsa', mod='TalmagePotts/strongs')

# Access features
for lex_node in F.otype.s('lex')[:10]:
    strongs_num = F.strongs.v(lex_node)
    glosses = F.strongs_glosses.v(lex_node)
    hebrew = F.voc_lex_utf8.v(lex_node)
    
    if strongs_num:
        print(f"{hebrew} → {strongs_num}: {glosses}")
```

## Coverage

- High-confidence matches (score ≥0.9): ~7,300 lexemes
- Based on OpenScriptures Strong's Hebrew Concordance

## Source

Generated from Strong's to BHSA mapping created with Hebrew text normalization and fuzzy matching.

## Version

1.0 (2025-11-21)
""")
    
    print(f"✓ Created {readme_path}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Strong's Concordance TF Feature Generator")
    print("=" * 60)
    
    # Load mappings
    strongs_mapping = load_mappings()
    
    # Create feature dictionaries
    strongs_dict, glosses_dict = create_feature_dicts(strongs_mapping, min_score=0.9)
    
    # Determine output directory
    home = Path.home()
    output_dir = home / 'text-fabric-data/github/TalmagePotts/strongs/tf/1.0'
    
    # Write TF features
    write_tf_features(strongs_dict, glosses_dict, output_dir)
    
    # Create config and README
    create_config_yaml(output_dir)
    create_readme(output_dir)
    
    print("\n" + "=" * 60)
    print("✓ TF Features Generated Successfully!")
    print("=" * 60)
    print(f"\nOutput location: {output_dir}")
    print("\nTo use:")
    print("  from tf.app import use")
    print("  A = use('etcbc/bhsa', mod='TalmagePotts/strongs')")
    print("=" * 60)


if __name__ == '__main__':
    main()
