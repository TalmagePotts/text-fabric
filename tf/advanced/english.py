"""
# English Translation Support

Provides English translations for BHSA Hebrew text using the Berean Study Bible (BSB)
alignment data from the OpenHebrewBible project.

This module integrates with Text-Fabric's rendering system to display English
translations alongside Hebrew text in query results and passage displays.
"""

import json
import os
from functools import lru_cache
from .english_config import get_translation_paths


class EnglishTranslation:
    """Lazy-loading English translation provider for BHSA nodes.
    
    Uses BSB translations from OpenHebrewBible CSV data with offset corrections
    to map BHSA node IDs to English words.
    
    Attributes
    ----------
    csv_path : str
        Path to BHSA-with-interlinear-translation.csv
    offset_path : str
        Path to bhsa_ohb_offsets.json
    enabled : bool
        Whether translations are available
    """
    
    def __init__(self, csv_path=None, offset_path=None):
        """Initialize the English translation provider.
        
        Parameters
        ----------
        csv_path : str, optional
            Path to translation CSV. If None, looks in English-lineup/ directory
        offset_path : str, optional
            Path to offset JSON. If None, looks in English-lineup/ directory
        """
        self.enabled = False
        self.csv_path = csv_path
        self.offset_path = offset_path
        self.offset_map = {}
        self._csv_file = None
        self._line_cache = {}
        
        # Try to find data files if not specified
        if csv_path is None or offset_path is None:
            self._find_data_files()
        
        # Load offset map if available
        if self.offset_path and os.path.exists(self.offset_path):
            self._load_offsets()
        
        # Check if CSV exists
        if self.csv_path and os.path.exists(self.csv_path):
            self.enabled = True
    
    def _find_data_files(self):
        """Try to locate translation data files in common locations."""
        # Use centralized configuration
        csv_path, offset_path = get_translation_paths()
        if csv_path and offset_path:
            self.csv_path = csv_path
            self.offset_path = offset_path
    
    def _load_offsets(self):
        """Load the offset map from JSON."""
        try:
            with open(self.offset_path, 'r') as f:
                offset_data = json.load(f)
                self.offset_map = {int(k): v for k, v in offset_data.items()}
        except Exception as e:
            print(f"Warning: Could not load offset map: {e}")
            self.offset_map = {}
    
    def _get_offset(self, bhsa_node):
        """Get the offset for a given BHSA node.
        
        Parameters
        ----------
        bhsa_node : int
            BHSA node ID
            
        Returns
        -------
        int
            Offset to apply to node ID for CSV lookup
        """
        offset = 0
        for node in sorted(self.offset_map.keys()):
            if bhsa_node >= node:
                offset = self.offset_map[node]
            else:
                break
        return offset
    
    @lru_cache(maxsize=1000)
    def _get_csv_line(self, line_num):
        """Get a specific line from the CSV file with caching.
        
        Parameters
        ----------
        line_num : int
            Line number to retrieve (1-indexed, but accounting for header row)
            
        Returns
        -------
        str or None
            The line content, or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                # Skip header row (line 0) and start counting from 1
                for i, line in enumerate(f):
                    if i == line_num:
                        return line.strip()
        except Exception:
            return None
        
        return None
    
    def get_translation(self, bhsa_node):
        """Get English translation for a BHSA node.
        
        Parameters
        ----------
        bhsa_node : int
            BHSA node ID (word node)
            
        Returns
        -------
        dict or None
            Dictionary with keys:
            - 'gloss': ETCBC gloss
            - 'english': BSB English translation
            - 'bsb_sort': BSB sort order (for reordering)
            Returns None if translation not available
        """
        if not self.enabled:
            return None
        
        offset = self._get_offset(bhsa_node)
        csv_idx = bhsa_node + offset
        
        line = self._get_csv_line(csv_idx)
        if not line:
            return None
        
        parts = line.split('\t')
        if len(parts) < 3:
            return None
        
        gloss = parts[2] if len(parts) > 2 else ''
        bsb_field = parts[3] if len(parts) > 3 else ''
        
        # Parse BSB field: format is ?1?In?
        english_text = ''
        bsb_sort = None
        if bsb_field:
            # Strip the brackets ??
            inner = bsb_field[1:-1] if len(bsb_field) > 2 else bsb_field
            # Split on full-width @ (?)
            if '\uff20' in inner:
                split_parts = inner.split('\uff20')
                if len(split_parts) == 2:
                    try:
                        bsb_sort = int(split_parts[0])
                    except ValueError:
                        pass
                    english_text = split_parts[1]
        
        return {
            'gloss': gloss,
            'english': english_text,
            'bsb_sort': bsb_sort
        }
    
    def get_verse_translation(self, word_nodes):
        """Get English translation for a sequence of words.
        
        Reorders words according to BSB sort order for natural English.
        
        Parameters
        ----------
        word_nodes : list of int
            List of BHSA word node IDs
            
        Returns
        -------
        str
            English translation with words in BSB order
        """
        if not self.enabled:
            return ""
        
        words_with_sort = []
        
        for node in word_nodes:
            trans = self.get_translation(node)
            if trans and trans['english']:
                text = trans['english']
                bsb_sort = trans['bsb_sort']
                
                # Use BSB sort order if available, otherwise use node order
                sort_key = bsb_sort if bsb_sort is not None else node
                words_with_sort.append((sort_key, text))
        
        # Sort by the sort key (BSB order)
        words_with_sort.sort(key=lambda x: x[0])
        
        # Return just the text in sorted order
        return ' '.join([text for _, text in words_with_sort])


# Global instance
_english_translation = None


def get_english_provider(csv_path=None, offset_path=None):
    """Get or create the global English translation provider.
    
    Parameters
    ----------
    csv_path : str, optional
        Path to translation CSV
    offset_path : str, optional
        Path to offset JSON
        
    Returns
    -------
    EnglishTranslation
        The translation provider instance
    """
    global _english_translation
    
    if _english_translation is None:
        _english_translation = EnglishTranslation(csv_path, offset_path)
    
    return _english_translation
