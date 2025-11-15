#!/usr/bin/env python3
import os
from tf.fabric import Fabric
from kjv_align import KJV_Align
from termcolor import cprint

# Configuration
BHSA_DIR = './bhsa/tf/2021'

def query_bible():
    """
    A simple CLI to query the Bible and see aligned English text from OpenHebrewBible.
    """
    
    print("Loading data...")
    
    # Check if the BHSA data directory exists
    if not os.path.exists(BHSA_DIR):
        print(f"Error: The BHSA data directory was not found at {BHSA_DIR}")
        return
    
    # Load the BHSA data
    TF = Fabric(locations=BHSA_DIR)
    api = TF.load('book chapter verse')
    
    if not api or not hasattr(api.F, 'otype'):
        print("Failed to load BHSA data")
        return
        
    print("\n✓ Data loaded successfully!")
    
    # Load the alignment module
    kjv_align = KJV_Align()
    
    # Start the query loop
    while True:
        query = input("\nEnter a Text-Fabric query (or 'quit'): ")
        
        if query.lower() == 'quit':
            break
            
        try:
            # Handle semicolon-delimited multi-line queries
            query = '\n'.join(query.split(';'))
            
            try:
                results = list(api.S.search(query))
            except Exception as e:
                print(f"Invalid query: {e}")
                continue
            
            if not results:
                print("No results found.")
                continue
                
            for result in results:
                # Get the book, chapter, and verse for the result
                book, chapter, verse = api.T.sectionFromNode(result[0])
                
                # Get the word nodes for the result
                word_nodes = result
                
                # Get the BHSA text
                bhsa_text = api.T.text(result)
                
                # Get the aligned English text
                aligned_text = kjv_align.get_aligned_text(book, chapter, verse, word_nodes)
                
                print(f"\nBHSA: {bhsa_text}")
                print(f"English: {aligned_text}")
                
        except Exception as e:
            print(f"An error occurred during the query: {e}")

if __name__ == '__main__':
    query_bible()