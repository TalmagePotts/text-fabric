"""
# English Translation Configuration

Configuration for English translation data paths.
Users can set environment variables or create a config file to specify
custom locations for translation data.
"""

import os
from pathlib import Path


def get_translation_paths():
    """Get paths to translation data files from environment or defaults.
    
    Checks the following locations in order:
    1. Environment variables TF_ENGLISH_CSV and TF_ENGLISH_OFFSET
    2. English-lineup/ directory relative to current working directory
    3. English-lineup/ directory relative to text-fabric package
    4. User's home directory ~/code/text-fabric/English-lineup/
    
    Returns
    -------
    tuple
        (csv_path, offset_path) or (None, None) if not found
    """
    # Check environment variables first
    csv_env = os.getenv('TF_ENGLISH_CSV')
    offset_env = os.getenv('TF_ENGLISH_OFFSET')
    
    if csv_env and offset_env:
        if os.path.exists(csv_env) and os.path.exists(offset_env):
            return (csv_env, offset_env)
    
    # Try common locations
    search_dirs = [
        Path.cwd() / 'English-lineup',
        Path(__file__).parent.parent.parent / 'English-lineup',
        Path.home() / 'code' / 'text-fabric' / 'English-lineup',
    ]
    
    for base_dir in search_dirs:
        csv_path = base_dir / 'BHSA-with-interlinear-translation.csv'
        offset_path = base_dir / 'bhsa_ohb_offsets.json'
        
        if csv_path.exists() and offset_path.exists():
            return (str(csv_path), str(offset_path))
    
    return (None, None)


def set_translation_paths(csv_path, offset_path):
    """Set custom translation data paths via environment variables.
    
    Parameters
    ----------
    csv_path : str
        Path to BHSA-with-interlinear-translation.csv
    offset_path : str
        Path to bhsa_ohb_offsets.json
    """
    os.environ['TF_ENGLISH_CSV'] = csv_path
    os.environ['TF_ENGLISH_OFFSET'] = offset_path
