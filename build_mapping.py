"""
Build Complete Mapping Between Strong's Numbers and BHSA Lexeme Nodes

This script creates a comprehensive mapping between Strong's Concordance Hebrew
entries and BHSA (Biblia Hebraica Stuttgartensia Amstelodamensis) lexeme nodes.

Usage:
    python3 build_mapping.py

Outputs:
    - strongs_to_bhsa.json: Complete mapping with confidence scores
    - ambiguous_mappings.json: Cases needing manual review
    - mapping_stats.txt: Coverage statistics
"""

import json
import re
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict

# Import our Hebrew normalizer
from hebrew_normalizer import (
    normalize_hebrew,
    compare_hebrew,
    extract_strongs_hebrew,
    is_hebrew_text
)


class MappingBuilder:
    """Build mapping between Strong's and BHSA."""
    
    def __init__(self, strongs_path: str, use_bhsa: bool = True):
        """
        Initialize the mapping builder.
        
        Args:
            strongs_path: Path to Strong's JSON file
            use_bhsa: Whether to load BHSA (requires Text-Fabric)
        """
        self.strongs_path = strongs_path
        self.use_bhsa = use_bhsa
        self.strongs_data = {}
        self.bhsa_lexemes = []
        self.bhsa_index = {}  # Index by normalized Hebrew for fast lookup
        self.F = None
        self.mapping = {}
        self.stats = {
            'total_strongs': 0,
            'matched': 0,
            'unmatched': 0,
            'ambiguous': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0
        }
    
    def load_strongs_data(self) -> None:
        """Load Strong's Hebrew dictionary from JSON file."""
        print(f"Loading Strong's data from {self.strongs_path}...")
        
        try:
            with open(self.strongs_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Handle JavaScript format (var strongsHebrewDictionary = {...})
                if 'var ' in content or 'strongsHebrewDictionary' in content:
                    # Extract JSON object from JavaScript
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start == -1 or end == 0:
                        raise ValueError("Could not find JSON object in file")
                    json_str = content[start:end]
                    self.strongs_data = json.loads(json_str)
                else:
                    self.strongs_data = json.loads(content)
            
            self.stats['total_strongs'] = len(self.strongs_data)
            print(f"✓ Loaded {self.stats['total_strongs']} Strong's entries")
            
        except FileNotFoundError:
            print(f"✗ Error: File not found: {self.strongs_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing JSON: {e}")
            sys.exit(1)
    
    def load_bhsa_data(self) -> None:
        """Load BHSA lexeme data directly from .tf files."""
        if not self.use_bhsa:
            print("Skipping BHSA load (demo mode)")
            return
        
        print("Loading BHSA data from .tf files...")
        
        bhsa_path = '/home/teapot/text-fabric-data/github/ETCBC/bhsa/tf/2021'
        
        if not os.path.exists(bhsa_path):
            print(f"  BHSA path not found: {bhsa_path}")
            print("  Continuing in demo mode...")
            self.use_bhsa = False
            return
        
        try:
            # Load word-level lexeme data (nodes 1-426590 are words)
            print(f"  Loading word-level lexeme data...")
            
            lex_utf8_file = os.path.join(bhsa_path, 'lex_utf8.tf')
            voc_lex_utf8_file = os.path.join(bhsa_path, 'voc_lex_utf8.tf')
            language_file = os.path.join(bhsa_path, 'language.tf')
            
            # Read all lines
            with open(lex_utf8_file, 'r', encoding='utf-8') as f:
                lex_lines = [l.strip() for l in f if l.strip() and not l.startswith('@')]
            
            with open(voc_lex_utf8_file, 'r', encoding='utf-8') as f:
                voc_lex_lines = [l.strip() for l in f if l.strip() and not l.startswith('@')]
            
            with open(language_file, 'r', encoding='utf-8') as f:
                lang_lines = [l.strip() for l in f if l.strip() and not l.startswith('@')]
            
            # Extract unique lexemes from word data (first 426590 lines)
            print(f"  Extracting unique lexemes from {min(len(lex_lines), 426590)} words...")
            
            lexeme_map = {}  # Map normalized form to lexeme data
            
            for i in range(min(len(lex_lines), 426590)):
                lex = lex_lines[i] if i < len(lex_lines) else ''
                voc_lex = voc_lex_lines[i] if i < len(voc_lex_lines) else ''
                lang = lang_lines[i] if i < len(lang_lines) else 'Hebrew'
                
                if lex or voc_lex:
                    # Use vocalized form as key for uniqueness
                    key = voc_lex or lex
                    if key not in lexeme_map:
                        normalized = normalize_hebrew(voc_lex or lex)
                        lexeme_map[key] = {
                            'node': i + 1,  # Pseudo-node (first occurrence)
                            'lex_utf8': lex,
                            'voc_lex_utf8': voc_lex,
                            'language': lang,
                            'normalized': normalized
                        }
            
            # Convert to list
            self.bhsa_lexemes = list(lexeme_map.values())
            
            # Build index for fast lookups
            print(f"  Building search index...")
            for lex in self.bhsa_lexemes:
                norm = lex['normalized']
                if norm not in self.bhsa_index:
                    self.bhsa_index[norm] = []
                self.bhsa_index[norm].append(lex)
            
            print(f"✓ Loaded {len(self.bhsa_lexemes)} unique BHSA lexemes")
            print(f"✓ Built index with {len(self.bhsa_index)} unique normalized forms")
            
        except Exception as e:
            print(f"✗ Error loading BHSA: {e}")
            import traceback
            traceback.print_exc()
            print("  Continuing in demo mode...")
            self.use_bhsa = False
    
    def clean_kjv_glosses(self, kjv_def: str) -> Tuple[str, List[str]]:
        """
        Clean and normalize KJV glosses.
        
        Args:
            kjv_def: Raw KJV definition string
            
        Returns:
            Tuple of (cleaned_string, list_of_glosses)
        """
        if not kjv_def:
            return '', []
        
        # Remove special markers like [idiom], [phrase], X, +
        cleaned = re.sub(r'\[idiom\]|\[phrase\]|[X+×]', '', kjv_def)
        
        # Split by comma
        parts = cleaned.split(',')
        
        # Clean each part
        glosses = []
        for part in parts:
            # Remove parentheses and their contents
            part = re.sub(r'\([^)]*\)', '', part)
            # Remove extra whitespace
            part = part.strip()
            # Convert to lowercase
            part = part.lower()
            # Remove punctuation except hyphens
            part = re.sub(r'[^\w\s-]', '', part)
            
            if part and len(part) > 1:  # Skip single characters
                glosses.append(part)
        
        # Create comma-separated string
        gloss_string = ','.join(glosses)
        
        return gloss_string, glosses
    
    def find_bhsa_matches(self, strongs_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find matching BHSA lexemes for a Strong's entry using indexed lookup.
        
        Args:
            strongs_entry: Strong's dictionary entry
            
        Returns:
            List of matches with scores
        """
        if not self.use_bhsa or not self.bhsa_index:
            return []
        
        # Extract and normalize Strong's Hebrew
        strongs_hebrew = extract_strongs_hebrew(strongs_entry)
        
        if not strongs_hebrew:
            return []
        
        matches = []
        
        # Fast lookup: exact normalized match
        exact_matches = self.bhsa_index.get(strongs_hebrew, [])
        
        for bhsa_lex in exact_matches:
            score = compare_hebrew(strongs_hebrew, bhsa_lex['normalized'])
            if score >= 0.7:
                matches.append({
                    'node': bhsa_lex['node'],
                    'score': round(score, 3),
                    'bhsa_lex': bhsa_lex['lex_utf8'],
                    'bhsa_voc': bhsa_lex['voc_lex_utf8'],
                    'language': bhsa_lex['language']
                })
        
        # If no exact matches, try fuzzy matching on similar forms
        if not matches:
            # Check forms that differ by 1-2 characters
            for norm_form, bhsa_list in self.bhsa_index.items():
                if abs(len(norm_form) - len(strongs_hebrew)) <= 2:
                    for bhsa_lex in bhsa_list:
                        score = compare_hebrew(strongs_hebrew, bhsa_lex['normalized'])
                        if score >= 0.7:
                            matches.append({
                                'node': bhsa_lex['node'],
                                'score': round(score, 3),
                                'bhsa_lex': bhsa_lex['lex_utf8'],
                                'bhsa_voc': bhsa_lex['voc_lex_utf8'],
                                'language': bhsa_lex['language']
                            })
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Limit to top 10 matches to avoid clutter
        return matches[:10]
    
    def process_strongs_entry(self, strongs_num: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single Strong's entry.
        
        Args:
            strongs_num: Strong's number (e.g., 'H157')
            entry: Strong's entry data
            
        Returns:
            Processed mapping entry
        """
        # Extract Hebrew lemma
        strongs_lemma = entry.get('lemma', '')
        strongs_normalized = normalize_hebrew(strongs_lemma)
        
        # Extract and clean KJV glosses
        kjv_def = entry.get('kjv_def', '')
        gloss_string, gloss_list = self.clean_kjv_glosses(kjv_def)
        
        # Find BHSA matches
        bhsa_matches = self.find_bhsa_matches(entry)
        
        # Determine confidence level
        if bhsa_matches:
            best_score = bhsa_matches[0]['score']
            if best_score >= 0.95:
                confidence = 'high'
                self.stats['high_confidence'] += 1
            elif best_score >= 0.85:
                confidence = 'medium'
                self.stats['medium_confidence'] += 1
            else:
                confidence = 'low'
                self.stats['low_confidence'] += 1
            
            if len(bhsa_matches) > 1:
                self.stats['ambiguous'] += 1
            
            self.stats['matched'] += 1
        else:
            confidence = 'none'
            self.stats['unmatched'] += 1
        
        # Build mapping entry
        mapping_entry = {
            'strongs_number': strongs_num,
            'strongs_lemma': strongs_lemma,
            'strongs_normalized': strongs_normalized,
            'bhsa_matches': bhsa_matches,
            'kjv_glosses': gloss_string,
            'gloss_list': gloss_list,
            'confidence': confidence,
            'match_count': len(bhsa_matches)
        }
        
        return mapping_entry
    
    def build_mapping(self) -> None:
        """Build the complete mapping."""
        print(f"\nBuilding mapping for {self.stats['total_strongs']} entries...")
        print("=" * 60)
        
        # Process each Strong's entry
        for i, (strongs_num, entry) in enumerate(self.strongs_data.items(), 1):
            # Progress indicator
            if i % 100 == 0:
                print(f"Progress: {i}/{self.stats['total_strongs']} "
                      f"({100*i/self.stats['total_strongs']:.1f}%)")
            
            # Process entry
            mapping_entry = self.process_strongs_entry(strongs_num, entry)
            self.mapping[strongs_num] = mapping_entry
        
        print(f"✓ Completed mapping for {len(self.mapping)} entries")
    
    def generate_outputs(self, output_dir: str = '.') -> None:
        """
        Generate output files.
        
        Args:
            output_dir: Directory for output files
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print("\nGenerating output files...")
        
        # 1. Complete mapping
        mapping_file = output_path / 'strongs_to_bhsa.json'
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(self.mapping, f, ensure_ascii=False, indent=2)
        print(f"✓ Created {mapping_file}")
        
        # 2. Ambiguous mappings (for manual review)
        ambiguous = {
            k: v for k, v in self.mapping.items()
            if v['confidence'] in ['medium', 'low'] or v['match_count'] > 1
        }
        
        ambiguous_file = output_path / 'ambiguous_mappings.json'
        with open(ambiguous_file, 'w', encoding='utf-8') as f:
            json.dump(ambiguous, f, ensure_ascii=False, indent=2)
        print(f"✓ Created {ambiguous_file} ({len(ambiguous)} entries)")
        
        # 3. Statistics
        stats_file = output_path / 'mapping_stats.txt'
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("Strong's to BHSA Mapping Statistics\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Total Strong's entries: {self.stats['total_strongs']}\n")
            f.write(f"Matched entries: {self.stats['matched']} "
                   f"({100*self.stats['matched']/self.stats['total_strongs']:.1f}%)\n")
            f.write(f"Unmatched entries: {self.stats['unmatched']} "
                   f"({100*self.stats['unmatched']/self.stats['total_strongs']:.1f}%)\n")
            f.write("\n")
            
            f.write("Confidence Levels:\n")
            f.write(f"  High (≥0.95): {self.stats['high_confidence']}\n")
            f.write(f"  Medium (0.85-0.94): {self.stats['medium_confidence']}\n")
            f.write(f"  Low (<0.85): {self.stats['low_confidence']}\n")
            f.write("\n")
            
            f.write(f"Ambiguous mappings (multiple matches): {self.stats['ambiguous']}\n")
            f.write("\n")
            
            # Validation warnings
            coverage = 100 * self.stats['matched'] / self.stats['total_strongs']
            if coverage < 90:
                f.write(f"⚠ WARNING: Coverage is {coverage:.1f}% (target: >90%)\n")
            else:
                f.write(f"✓ Coverage: {coverage:.1f}% (target met)\n")
            
            # List unmatched entries
            if self.stats['unmatched'] > 0:
                f.write("\nUnmatched Strong's Numbers:\n")
                f.write("-" * 60 + "\n")
                for strongs_num, entry in self.mapping.items():
                    if entry['confidence'] == 'none':
                        f.write(f"{strongs_num}: {entry['strongs_lemma']} "
                               f"({entry['kjv_glosses'][:50]}...)\n")
            
            # List medium confidence matches
            if self.stats['medium_confidence'] > 0:
                f.write("\nMedium Confidence Matches (0.85-0.94):\n")
                f.write("-" * 60 + "\n")
                for strongs_num, entry in self.mapping.items():
                    if entry['confidence'] == 'medium':
                        best_match = entry['bhsa_matches'][0] if entry['bhsa_matches'] else None
                        if best_match:
                            f.write(f"{strongs_num}: {entry['strongs_lemma']} → "
                                   f"{best_match['bhsa_voc']} (score: {best_match['score']})\n")
        
        print(f"✓ Created {stats_file}")
    
    def print_summary(self) -> None:
        """Print summary statistics."""
        print("\n" + "=" * 60)
        print("MAPPING SUMMARY")
        print("=" * 60)
        
        coverage = 100 * self.stats['matched'] / self.stats['total_strongs']
        
        print(f"Total Strong's entries: {self.stats['total_strongs']}")
        print(f"Matched: {self.stats['matched']} ({coverage:.1f}%)")
        print(f"Unmatched: {self.stats['unmatched']}")
        print()
        print("Confidence Distribution:")
        print(f"  High (≥0.95): {self.stats['high_confidence']}")
        print(f"  Medium (0.85-0.94): {self.stats['medium_confidence']}")
        print(f"  Low (<0.85): {self.stats['low_confidence']}")
        print()
        print(f"Ambiguous (multiple matches): {self.stats['ambiguous']}")
        print()
        
        # Validation
        if coverage >= 90:
            print("✓ Coverage target met (>90%)")
        else:
            print(f"⚠ WARNING: Coverage is {coverage:.1f}% (target: >90%)")
        
        if self.stats['unmatched'] > 0:
            print(f"⚠ {self.stats['unmatched']} entries have no matches")
        
        if self.stats['medium_confidence'] > 0:
            print(f"⚠ {self.stats['medium_confidence']} entries need verification")
        
        print("=" * 60)


def main():
    """Main entry point."""
    print("Strong's to BHSA Mapping Builder")
    print("=" * 60)
    
    # Determine Strong's path
    strongs_path = Path('strongs/hebrew/strongs-hebrew-dictionary.js')
    
    if not strongs_path.exists():
        print(f"✗ Error: Strong's file not found at {strongs_path}")
        print("  Please ensure the file exists or update the path")
        sys.exit(1)
    
    # Check if BHSA should be loaded
    use_bhsa = True
    try:
        import tf
    except ImportError:
        print("⚠ Text-Fabric not available - running in demo mode")
        print("  Only Strong's data will be processed")
        use_bhsa = False
    
    # Build mapping
    builder = MappingBuilder(str(strongs_path), use_bhsa=use_bhsa)
    
    try:
        builder.load_strongs_data()
        
        if use_bhsa:
            builder.load_bhsa_data()
        
        builder.build_mapping()
        builder.generate_outputs()
        builder.print_summary()
        
        print("\n✓ Mapping complete!")
        print("  Output files:")
        print("    - strongs_to_bhsa.json")
        print("    - ambiguous_mappings.json")
        print("    - mapping_stats.txt")
        
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
