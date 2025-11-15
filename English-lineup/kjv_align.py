from tf.fabric import Fabric
import json

BHSA_DIR = './bhsa/tf/2021'
OHB_CSV_FILE = 'BHSA-with-interlinear-translation.csv'
OFFSET_MAP_FILE = 'bhsa_ohb_offsets.json'

class KJV_Align:
    def __init__(self):
        # Load BHSA for fallback glosses
        TF = Fabric(locations=BHSA_DIR)
        self.api = TF.load('gloss')
        
        # Load OpenHebrewBible CSV
        with open(OHB_CSV_FILE, 'r', encoding='utf-8') as f:
            self.ohb_lines = f.readlines()
        
        # Load offset map
        with open(OFFSET_MAP_FILE, 'r') as f:
            offset_data = json.load(f)
            self.offset_map = {int(k): v for k, v in offset_data.items()}
    
    def _get_offset(self, bhsa_node):
        """Get the offset for a given BHSA node"""
        offset = 0
        for node in sorted(self.offset_map.keys()):
            if bhsa_node >= node:
                offset = self.offset_map[node]
            else:
                break
        return offset
    
    def _get_ohb_data(self, bhsa_node):
        """Get OpenHebrewBible data for a BHSA node"""
        offset = self._get_offset(bhsa_node)
        csv_idx = bhsa_node + offset
        
        if csv_idx < 1 or csv_idx >= len(self.ohb_lines):
            return None
        
        parts = self.ohb_lines[csv_idx].strip().split('\t')
        if len(parts) < 3:
            return None
        
        gloss = parts[2] if len(parts) > 2 else ''
        bsb_field = parts[3] if len(parts) > 3 else ''
        
        # Parse BSB field: format is 〔1＠In〕
        english_text = ''
        bsb_sort = None
        if bsb_field:
            # The field uses special brackets 〔〕 and full-width @ (＠)
            # Strip the brackets
            inner = bsb_field[1:-1] if len(bsb_field) > 2 else bsb_field
            # Split on full-width @
            if '\uff20' in inner:  # Unicode for ＠
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
    
    def get_aligned_text(self, book, chapter, verse, word_nodes, all_verse_words=None):
        """
        Get English translations for the given word nodes.
        Uses BSB translations from OpenHebrewBible.
        Only includes words that have BSB translations.
        """
        words_with_sort = []
        
        for node in word_nodes:
            # Try to get BSB translation from OHB
            ohb_data = self._get_ohb_data(node)
            if ohb_data and ohb_data['english']:
                text = ohb_data['english']
                bsb_sort = ohb_data['bsb_sort']
                
                # Use BSB sort order if available, otherwise use node order
                sort_key = bsb_sort if bsb_sort is not None else node
                words_with_sort.append((sort_key, text))
        
        # Sort by the sort key (BSB order)
        words_with_sort.sort(key=lambda x: x[0])
        
        # Return just the text in sorted order
        return ' '.join([text for _, text in words_with_sort])

def load_module():
    return KJV_Align()
