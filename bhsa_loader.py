"""
Direct BHSA Data Loader

Loads BHSA lexeme data directly from .tf files without requiring pyyaml.
This is a simplified loader for the mapping task.
"""

import os
from typing import Dict, List, Tuple


class SimpleBHSALoader:
    """Simple loader for BHSA .tf files."""
    
    def __init__(self, bhsa_path: str):
        """
        Initialize loader.
        
        Args:
            bhsa_path: Path to BHSA tf directory
        """
        self.bhsa_path = bhsa_path
        self.lex_nodes = []
        self.lex_utf8 = {}
        self.voc_lex_utf8 = {}
        self.language = {}
    
    def load_tf_file(self, filename: str) -> Dict[int, str]:
        """
        Load a simple .tf file.
        
        Args:
            filename: Name of .tf file
            
        Returns:
            Dictionary mapping node numbers to values
        """
        filepath = os.path.join(self.bhsa_path, filename)
        data = {}
        
        if not os.path.exists(filepath):
            print(f"  Warning: {filename} not found")
            return data
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip header lines (start with @)
            content_start = 0
            for i, line in enumerate(lines):
                if not line.startswith('@'):
                    content_start = i
                    break
            
            # Parse data lines
            current_node = None
            for line in lines[content_start:]:
                line = line.strip()
                if not line:
                    continue
                
                # Node range or single node
                if '\t' in line:
                    parts = line.split('\t')
                    if len(parts) == 2:
                        node_spec, value = parts
                        
                        # Handle node ranges (e.g., "1-100")
                        if '-' in node_spec:
                            start, end = map(int, node_spec.split('-'))
                            for node in range(start, end + 1):
                                data[node] = value
                        else:
                            # Single node
                            node = int(node_spec)
                            data[node] = value
                            current_node = node
                elif current_node is not None:
                    # Continuation of previous value
                    data[current_node] += '\n' + line
        
        except Exception as e:
            print(f"  Error loading {filename}: {e}")
        
        return data
    
    def load_otype(self) -> Dict[str, List[int]]:
        """
        Load otype.tf to get lexeme nodes.
        
        Returns:
            Dictionary mapping types to node lists
        """
        filepath = os.path.join(self.bhsa_path, 'otype.tf')
        otypes = {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip header
            content_start = 0
            for i, line in enumerate(lines):
                if not line.startswith('@'):
                    content_start = i
                    break
            
            # Parse otype data
            for line in lines[content_start:]:
                line = line.strip()
                if not line or not '\t' in line:
                    continue
                
                parts = line.split('\t')
                if len(parts) == 2:
                    node_spec, otype = parts
                    
                    if otype not in otypes:
                        otypes[otype] = []
                    
                    # Handle ranges
                    if '-' in node_spec:
                        start, end = map(int, node_spec.split('-'))
                        otypes[otype].extend(range(start, end + 1))
                    else:
                        otypes[otype].append(int(node_spec))
        
        except Exception as e:
            print(f"  Error loading otype.tf: {e}")
        
        return otypes
    
    def load_lexemes(self) -> List[Dict]:
        """
        Load all lexeme data.
        
        Returns:
            List of lexeme dictionaries
        """
        print("  Loading otype.tf...")
        otypes = self.load_otype()
        self.lex_nodes = otypes.get('lex', [])
        print(f"  Found {len(self.lex_nodes)} lexeme nodes")
        
        print("  Loading lex_utf8.tf...")
        self.lex_utf8 = self.load_tf_file('lex_utf8.tf')
        print(f"  Loaded {len(self.lex_utf8)} lex_utf8 values")
        
        print("  Loading voc_lex_utf8.tf...")
        self.voc_lex_utf8 = self.load_tf_file('voc_lex_utf8.tf')
        print(f"  Loaded {len(self.voc_lex_utf8)} voc_lex_utf8 values")
        
        print("  Loading language.tf...")
        self.language = self.load_tf_file('language.tf')
        print(f"  Loaded {len(self.language)} language values")
        
        # Build lexeme list
        lexemes = []
        for node in self.lex_nodes:
            lex = self.lex_utf8.get(node, '')
            voc_lex = self.voc_lex_utf8.get(node, '')
            lang = self.language.get(node, 'Hebrew')
            
            if lex or voc_lex:
                lexemes.append({
                    'node': node,
                    'lex_utf8': lex,
                    'voc_lex_utf8': voc_lex,
                    'language': lang
                })
        
        print(f"  Built {len(lexemes)} lexeme entries")
        return lexemes


def test_loader():
    """Test the loader."""
    bhsa_path = '/home/teapot/text-fabric-data/github/ETCBC/bhsa/tf/2021'
    
    if not os.path.exists(bhsa_path):
        print(f"BHSA path not found: {bhsa_path}")
        return
    
    print("Testing SimpleBHSALoader...")
    print("=" * 60)
    
    loader = SimpleBHSALoader(bhsa_path)
    lexemes = loader.load_lexemes()
    
    print("\nSample lexemes:")
    print("=" * 60)
    for lex in lexemes[:10]:
        print(f"Node {lex['node']}:")
        print(f"  lex_utf8: {lex['lex_utf8']}")
        print(f"  voc_lex_utf8: {lex['voc_lex_utf8']}")
        print(f"  language: {lex['language']}")
        print()
    
    print(f"Total lexemes loaded: {len(lexemes)}")


if __name__ == '__main__':
    test_loader()
