"""
Strong's Search Library for Text-Fabric

English-based search for Hebrew Bible using Strong's glosses.

Features:
- Search Hebrew words by English translation
- Semantic field analysis
- Translation variety metrics
- Frequency analysis
- Export capabilities

Example:
    from strongs_search_lib import StrongsSearch
    
    search = StrongsSearch()
    results = search.search_by_gloss("love")
    for r in results:
        print(f"{r['hebrew']} ({r['strongs']}): {r['all_glosses']}")
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
import re


class StrongsSearch:
    """
    English-based search for Hebrew Bible using Strong's glosses.
    
    This class provides comprehensive search and analysis capabilities
    for finding Hebrew words by their English translations from Strong's
    Concordance.
    """
    
    def __init__(self, mapping_file: Optional[str] = None):
        """
        Initialize StrongsSearch.
        
        Args:
            mapping_file: Path to strongs_to_bhsa.json (optional)
                         If not provided, uses default location
        """
        if mapping_file is None:
            # Try to find mapping file
            script_dir = Path(__file__).parent
            # Check if we're in strongs-mapping directory
            if script_dir.name == 'strongs-mapping':
                mapping_file = script_dir / 'data/strongs_to_bhsa.json'
            else:
                # Assume we're in scripts subdirectory
                mapping_file = script_dir.parent / 'data/strongs_to_bhsa.json'
        
        self.mapping_file = Path(mapping_file)
        self.mapping = {}
        self.gloss_index = {}  # English term → list of Strong's numbers
        self.hebrew_index = {}  # Hebrew word → Strong's number
        
        self._load_data()
        self._build_indices()
    
    def _load_data(self):
        """Load Strong's to BHSA mapping data."""
        print(f"Loading mapping from {self.mapping_file}...")
        
        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)
        
        print(f"✓ Loaded {len(self.mapping)} Strong's entries")
    
    def _build_indices(self):
        """Build search indices for fast lookup."""
        print("Building search indices...")
        
        for strongs_num, entry in self.mapping.items():
            # Index by glosses
            for gloss in entry['gloss_list']:
                gloss_lower = gloss.lower().strip()
                if gloss_lower:
                    if gloss_lower not in self.gloss_index:
                        self.gloss_index[gloss_lower] = []
                    self.gloss_index[gloss_lower].append(strongs_num)
            
            # Index by Hebrew
            hebrew = entry['strongs_normalized']
            if hebrew:
                self.hebrew_index[hebrew] = strongs_num
        
        print(f"✓ Indexed {len(self.gloss_index)} unique English glosses")
        print(f"✓ Indexed {len(self.hebrew_index)} Hebrew words")
    
    def search_by_gloss(self, english_term: str, exact: bool = False) -> List[Dict]:
        """
        Find all Hebrew lexemes translated as this English term.
        
        Args:
            english_term: English word to search (e.g., "love")
            exact: If True, require exact match; if False, substring match
            
        Returns:
            List of dicts with: hebrew, strongs, all_glosses, match_count
            
        Example:
            >>> search = StrongsSearch()
            >>> results = search.search_by_gloss("love")
            >>> for r in results:
            ...     print(f"{r['hebrew']} ({r['strongs']}): {r['all_glosses']}")
        """
        term_lower = english_term.lower().strip()
        results = []
        
        if exact:
            # Exact match
            if term_lower in self.gloss_index:
                for strongs_num in self.gloss_index[term_lower]:
                    entry = self.mapping[strongs_num]
                    results.append({
                        'hebrew': entry['strongs_lemma'],
                        'strongs': strongs_num,
                        'all_glosses': entry['kjv_glosses'],
                        'gloss_list': entry['gloss_list'],
                        'match_count': len(entry['bhsa_matches']),
                        'confidence': entry['confidence']
                    })
        else:
            # Substring match
            for gloss, strongs_list in self.gloss_index.items():
                if term_lower in gloss:
                    for strongs_num in strongs_list:
                        entry = self.mapping[strongs_num]
                        if strongs_num not in [r['strongs'] for r in results]:
                            results.append({
                                'hebrew': entry['strongs_lemma'],
                                'strongs': strongs_num,
                                'all_glosses': entry['kjv_glosses'],
                                'gloss_list': entry['gloss_list'],
                                'match_count': len(entry['bhsa_matches']),
                                'confidence': entry['confidence'],
                                'matched_gloss': gloss
                            })
        
        # Sort by match count (most common first)
        results.sort(key=lambda x: x['match_count'], reverse=True)
        
        return results
    
    def semantic_field(self, gloss: str) -> Dict[str, Any]:
        """
        Map semantic field: all Hebrew words sharing this English gloss.
        
        Args:
            gloss: English gloss to analyze
            
        Returns:
            Dict with lexeme_groups, frequency_distribution, total_words
            
        Example:
            >>> search = StrongsSearch()
            >>> field = search.semantic_field("love")
            >>> print(f"Found {field['total_words']} Hebrew words for 'love'")
        """
        results = self.search_by_gloss(gloss, exact=True)
        
        # Group by frequency
        freq_dist = Counter()
        lexeme_groups = []
        
        for r in results:
            freq_dist[r['hebrew']] = r['match_count']
            lexeme_groups.append({
                'hebrew': r['hebrew'],
                'strongs': r['strongs'],
                'glosses': r['all_glosses'],
                'occurrences': r['match_count']
            })
        
        return {
            'english_gloss': gloss,
            'total_words': len(results),
            'lexeme_groups': lexeme_groups,
            'frequency_distribution': dict(freq_dist.most_common()),
            'most_common': lexeme_groups[0] if lexeme_groups else None
        }
    
    def translation_variety(self, top_n: int = 20) -> List[Tuple]:
        """
        Rank Hebrew words by translation variety.
        
        Args:
            top_n: Number of top results to return
            
        Returns:
            List of (hebrew_word, num_distinct_glosses, glosses_list, strongs)
            
        Example:
            >>> search = StrongsSearch()
            >>> variety = search.translation_variety(10)
            >>> for hebrew, count, glosses, strongs in variety:
            ...     print(f"{hebrew} ({strongs}): {count} translations")
        """
        variety_list = []
        
        for strongs_num, entry in self.mapping.items():
            hebrew = entry['strongs_lemma']
            gloss_list = entry['gloss_list']
            num_glosses = len(set(gloss_list))  # Unique glosses
            
            variety_list.append((
                hebrew,
                num_glosses,
                entry['kjv_glosses'],
                strongs_num
            ))
        
        # Sort by number of distinct glosses (descending)
        variety_list.sort(key=lambda x: x[1], reverse=True)
        
        return variety_list[:top_n]
    
    def reverse_lookup(self, strongs_number: str) -> Optional[Dict]:
        """
        Get full details for a Strong's number.
        
        Args:
            strongs_number: Strong's number (e.g., "H157")
            
        Returns:
            Dict with Hebrew, glosses, BHSA matches, statistics
            
        Example:
            >>> search = StrongsSearch()
            >>> info = search.reverse_lookup("H157")
            >>> print(f"{info['hebrew']}: {info['kjv_glosses']}")
        """
        if strongs_number not in self.mapping:
            return None
        
        entry = self.mapping[strongs_number]
        
        return {
            'strongs': strongs_number,
            'hebrew': entry['strongs_lemma'],
            'normalized': entry['strongs_normalized'],
            'kjv_glosses': entry['kjv_glosses'],
            'gloss_list': entry['gloss_list'],
            'bhsa_matches': entry['bhsa_matches'],
            'match_count': len(entry['bhsa_matches']),
            'confidence': entry['confidence']
        }
    
    def compare_translations(self, hebrew_lex: str) -> Optional[Dict]:
        """
        For a Hebrew word, show all KJV translation choices.
        
        Args:
            hebrew_lex: Hebrew word (normalized or with niqqud)
            
        Returns:
            Dict with Strong's number, all glosses, gloss breakdown
            
        Example:
            >>> search = StrongsSearch()
            >>> trans = search.compare_translations("אהב")
            >>> for gloss in trans['gloss_list']:
            ...     print(f"  - {gloss}")
        """
        # Try to find in Hebrew index
        strongs_num = self.hebrew_index.get(hebrew_lex)
        
        if not strongs_num:
            # Try searching in mapping directly
            for num, entry in self.mapping.items():
                if entry['strongs_normalized'] == hebrew_lex or entry['strongs_lemma'] == hebrew_lex:
                    strongs_num = num
                    break
        
        if not strongs_num:
            return None
        
        return self.reverse_lookup(strongs_num)
    
    def find_related_words(self, strongs_number: str, max_results: int = 10) -> List[Dict]:
        """
        Find Hebrew words with similar English glosses.
        
        Args:
            strongs_number: Strong's number to find related words for
            max_results: Maximum number of results
            
        Returns:
            List of related words with overlap scores
        """
        if strongs_number not in self.mapping:
            return []
        
        source_entry = self.mapping[strongs_number]
        source_glosses = set(source_entry['gloss_list'])
        
        related = []
        
        for num, entry in self.mapping.items():
            if num == strongs_number:
                continue
            
            target_glosses = set(entry['gloss_list'])
            overlap = source_glosses & target_glosses
            
            if overlap:
                overlap_score = len(overlap) / len(source_glosses)
                related.append({
                    'hebrew': entry['strongs_lemma'],
                    'strongs': num,
                    'shared_glosses': list(overlap),
                    'overlap_score': round(overlap_score, 3),
                    'all_glosses': entry['kjv_glosses']
                })
        
        # Sort by overlap score
        related.sort(key=lambda x: x['overlap_score'], reverse=True)
        
        return related[:max_results]
    
    def export_lexicon(self, format: str = 'csv', output_file: Optional[str] = None) -> str:
        """
        Export complete Hebrew→English glossary.
        
        Args:
            format: Output format ('csv', 'json', or 'markdown')
            output_file: Output filename (optional)
            
        Returns:
            Filename of exported data
            
        Example:
            >>> search = StrongsSearch()
            >>> filename = search.export_lexicon('csv')
            >>> print(f"Exported to {filename}")
        """
        if output_file is None:
            output_file = f"strongs_lexicon.{format}"
        
        if format == 'csv':
            import csv
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Strongs', 'Hebrew', 'Normalized', 'KJV_Glosses', 'Match_Count', 'Confidence'])
                
                for num, entry in sorted(self.mapping.items()):
                    writer.writerow([
                        num,
                        entry['strongs_lemma'],
                        entry['strongs_normalized'],
                        entry['kjv_glosses'],
                        len(entry['bhsa_matches']),
                        entry['confidence']
                    ])
        
        elif format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.mapping, f, ensure_ascii=False, indent=2)
        
        elif format == 'markdown':
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Strong's Hebrew Lexicon\n\n")
                f.write("| Strong's | Hebrew | KJV Glosses | Matches |\n")
                f.write("|----------|--------|-------------|----------|\n")
                
                for num, entry in sorted(self.mapping.items()):
                    f.write(f"| {num} | {entry['strongs_lemma']} | {entry['kjv_glosses'][:50]}... | {len(entry['bhsa_matches'])} |\n")
        
        else:
            raise ValueError(f"Unknown format: {format}")
        
        print(f"✓ Exported lexicon to {output_file}")
        return output_file
    
    def statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the mapping.
        
        Returns:
            Dict with various statistics
        """
        total_entries = len(self.mapping)
        with_matches = sum(1 for e in self.mapping.values() if e['bhsa_matches'])
        high_conf = sum(1 for e in self.mapping.values() if e['confidence'] == 'high')
        
        total_glosses = sum(len(e['gloss_list']) for e in self.mapping.values())
        avg_glosses = total_glosses / total_entries if total_entries > 0 else 0
        
        return {
            'total_strongs_entries': total_entries,
            'with_bhsa_matches': with_matches,
            'coverage': round(100 * with_matches / total_entries, 1),
            'high_confidence': high_conf,
            'unique_english_glosses': len(self.gloss_index),
            'total_glosses': total_glosses,
            'avg_glosses_per_word': round(avg_glosses, 1)
        }


# Example usage
if __name__ == '__main__':
    # Initialize search
    search = StrongsSearch()
    
    # Print statistics
    stats = search.statistics()
    print("\n" + "=" * 60)
    print("Strong's Search Library Statistics")
    print("=" * 60)
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Example searches
    print("\n" + "=" * 60)
    print("Example: Search for 'love'")
    print("=" * 60)
    results = search.search_by_gloss("love", exact=True)
    for r in results[:5]:
        print(f"{r['hebrew']:15} ({r['strongs']:6}): {r['all_glosses'][:50]}...")
    
    print("\n" + "=" * 60)
    print("Example: Translation variety (top 10)")
    print("=" * 60)
    variety = search.translation_variety(10)
    for hebrew, count, glosses, strongs in variety:
        print(f"{hebrew:15} ({strongs}): {count} translations - {glosses[:40]}...")
