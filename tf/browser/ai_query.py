"""
AI Query Generation Module for Text-Fabric BHSA Browser

This module provides AI-powered natural language to Text-Fabric query conversion
using Google's Gemini API with comprehensive context including lexeme database,
feature references, and validated examples.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# Module-level cache for lexemes
_LEXEMES_DF: Optional[pd.DataFrame] = None
_MODULE_DIR = Path(__file__).parent.parent.parent  # Go up to text-fabric root


def load_lexemes() -> pd.DataFrame:
    """Load and cache the BHSA lexeme database."""
    global _LEXEMES_DF
    
    if _LEXEMES_DF is not None:
        return _LEXEMES_DF
    
    lexeme_path = _MODULE_DIR / "bhsa_lexemes.csv"
    
    if not lexeme_path.exists():
        raise FileNotFoundError(f"Lexeme database not found at {lexeme_path}")
    
    _LEXEMES_DF = pd.read_csv(lexeme_path, encoding='utf-8')
    return _LEXEMES_DF


def search_lexemes(term: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    Search for lexemes by English gloss or Hebrew text.
    
    Args:
        term: Search term (English word or Hebrew)
        max_results: Maximum number of results to return
        
    Returns:
        List of matching lexemes with lex, sp, gloss, and voc_lex
    """
    df = load_lexemes()
    term_lower = term.lower().strip()
    
    # Search in gloss column (case-insensitive)
    matches = df[df['gloss'].str.lower().str.contains(term_lower, na=False, regex=False)]
    
    # Limit results
    matches = matches.head(max_results)
    
    # Convert to list of dicts
    results = []
    for _, row in matches.iterrows():
        results.append({
            'lex': str(row['lex']),
            'sp': str(row['sp']),
            'gloss': str(row['gloss']),
            'voc_lex': str(row['voc_lex']) if pd.notna(row['voc_lex']) else ''
        })
    
    return results


def build_system_prompt() -> str:
    """Build the comprehensive system prompt for the AI."""
    return """You are a Text-Fabric query generator for biblical Hebrew (BHSA corpus). Convert natural language to Text-Fabric search syntax.

## CRITICAL RULES
1. Use EXACT lexeme spelling from database (case-sensitive)
2. Feature names: sp, lex, gn, nu, ps, st, vs, vt, function, typ
3. Indentation = containment (2 spaces per level)
4. Part of speech: verb, subs, nmpr, adjv, advb, prep, conj, intj, art, prps, prde, prin, inrg, nega

## COMMON ERRORS - AVOID THESE
❌ word pos=verb → ✅ word sp=verb
❌ word lex=YHWH → ✅ word lex=JHWH/
❌ word lex=give → ✅ word lex=NTN[
❌ phrase typ=Pred → ✅ phrase function=Pred

## KEY FEATURES
- sp: verb, subs, nmpr, adjv, advb, prep, conj, intj, art, prps, prde, prin, inrg, nega
- lex: exact from database (e.g. NTN[, JHWH/, BR>[, >T)
- gn: m, f | nu: sg, pl, du | ps: p1, p2, p3
- st: a, c, e | vs: qal, nif, piel, pual, hif, hof, hith
- vt: perf, impf, wayq, coh, impv, infc, infa

## OPERATORS
< before | > after | :> immediately after | <: immediately before

## EXAMPLES

Find all verbs:
word sp=verb

Find YHWH:
word lex=JHWH/

Plural feminine nouns:
word sp=subs gn=f nu=pl

Verb "give" in qal:
word lex=NTN[ vs=qal

Verb followed by noun (same clause):
clause
  v:word sp=verb
  n:word sp=subs
  v < n

Verb immediately before noun:
sentence
  v:word sp=verb
  n:word sp=subs
  v :> n

Verb "give" with preposition "to" after:
clause
  w:word lex=NTN[
  l:word lex=L
  l :> w

## OUTPUT
Return ONLY the query. No explanations, no markdown blocks, no extra text. Use 2-space indentation."""


def build_user_prompt(user_input: str, lexemes: List[Dict[str, str]]) -> str:
    """Build the user prompt with injected lexeme context."""
    prompt_parts = []
    
    # Add lexeme database context if we found matches
    if lexemes:
        prompt_parts.append("## RELEVANT LEXEMES FROM DATABASE\n")
        for lex in lexemes:
            prompt_parts.append(
                f"- {lex['gloss']}: lex={lex['lex']} (sp={lex['sp']})"
            )
        prompt_parts.append("\n")
    
    # Add user request
    prompt_parts.append("## USER REQUEST\n")
    prompt_parts.append(user_input)
    
    return "\n".join(prompt_parts)


def extract_keywords(user_input: str) -> List[str]:
    """Extract potential Hebrew word references from user input."""
    # Common words to search for
    keywords = []
    
    # Extract quoted words
    quoted = re.findall(r'"([^"]+)"', user_input)
    keywords.extend(quoted)
    
    quoted_single = re.findall(r"'([^']+)'", user_input)
    keywords.extend(quoted_single)
    
    # Common biblical terms
    biblical_terms = [
        'give', 'create', 'say', 'see', 'make', 'go', 'come', 'take',
        'YHWH', 'God', 'lord', 'heaven', 'earth', 'man', 'woman',
        'day', 'night', 'light', 'darkness', 'water', 'land',
        'verb', 'noun', 'preposition', 'Lamed', 'to', 'in', 'from'
    ]
    
    user_lower = user_input.lower()
    for term in biblical_terms:
        if term.lower() in user_lower:
            keywords.append(term)
    
    return list(set(keywords))  # Remove duplicates


def validate_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate the generated query for basic syntax correctness.
    
    Returns:
        (is_valid, error_message)
    """
    lines = query.strip().split('\n')
    
    if not lines:
        return False, "Query is empty"
    
    # Check for common syntax errors
    for i, line in enumerate(lines, 1):
        # Check indentation (must be even number of spaces)
        leading_spaces = len(line) - len(line.lstrip(' '))
        if leading_spaces % 2 != 0:
            return False, f"Line {i}: Indentation must use multiples of 2 spaces"
        
        # Check for tabs
        if '\t' in line:
            return False, f"Line {i}: Use spaces, not tabs for indentation"
        
        # Check for common feature name errors
        if 'pos=' in line:
            return False, f"Line {i}: Use 'sp=' not 'pos=' for part of speech"
        
        if 'gender=' in line:
            return False, f"Line {i}: Use 'gn=' not 'gender=' for gender"
        
        if 'number=' in line:
            return False, f"Line {i}: Use 'nu=' not 'number=' for number"
    
    # Check first line is a valid node type
    first_line = lines[0].strip()
    valid_node_types = ['word', 'phrase', 'clause', 'sentence', 'verse', 'chapter', 'book']
    
    # Extract node type (may have name prefix like "w:word")
    node_type = first_line.split()[0].split(':')[-1]
    
    if node_type not in valid_node_types:
        return False, f"First line must start with a valid node type: {', '.join(valid_node_types)}"
    
    return True, None


def generate_query(user_prompt: str, api_key: str) -> Dict[str, any]:
    """
    Generate a Text-Fabric query from natural language using Gemini API.
    
    Args:
        user_prompt: Natural language description of desired query
        api_key: Google Gemini API key
        
    Returns:
        Dictionary with:
        - query: Generated Text-Fabric query string
        - explanation: Human-readable explanation
        - lexemes_used: List of lexemes found and used
        - error: Error message if generation failed
    """
    if not GENAI_AVAILABLE:
        return {
            'query': '',
            'explanation': '',
            'lexemes_used': [],
            'error': 'google-generativeai package not installed. Install with: pip install google-generativeai'
        }
    
    if not api_key:
        return {
            'query': '',
            'explanation': '',
            'lexemes_used': [],
            'error': 'API key is required'
        }
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Extract keywords and search for lexemes
        keywords = extract_keywords(user_prompt)
        all_lexemes = []
        for keyword in keywords:
            lexemes = search_lexemes(keyword, max_results=5)
            all_lexemes.extend(lexemes)
        
        # Remove duplicates
        seen = set()
        unique_lexemes = []
        for lex in all_lexemes:
            key = lex['lex']
            if key not in seen:
                seen.add(key)
                unique_lexemes.append(lex)
        
        # Build prompts
        system_prompt = build_system_prompt()
        user_prompt_with_context = build_user_prompt(user_prompt, unique_lexemes)
        
        # Combine system and user prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt_with_context}"
        
        # Generate query with low temperature for consistency
        try:
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=1024,
                ),
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE",
                    },
                ]
            )
        except Exception as api_error:
            return {
                'query': '',
                'explanation': '',
                'lexemes_used': [],
                'error': f'API error: {str(api_error)}'
            }
        
        # Check if response was blocked
        if not response.candidates:
            return {
                'query': '',
                'explanation': '',
                'lexemes_used': [],
                'error': 'Response was blocked by safety filters. Try rephrasing your query more simply.'
            }
        
        candidate = response.candidates[0]
        
        # Check finish reason
        if hasattr(candidate, 'finish_reason'):
            finish_reason = candidate.finish_reason
            # finish_reason: 1 = STOP (normal), 2 = MAX_TOKENS, 3 = SAFETY, 4 = RECITATION, 5 = OTHER
            if finish_reason == 3:  # SAFETY
                return {
                    'query': '',
                    'explanation': '',
                    'lexemes_used': [],
                    'error': 'Response blocked by safety filters. Try a simpler description.'
                }
            elif finish_reason == 2:  # MAX_TOKENS
                return {
                    'query': '',
                    'explanation': '',
                    'lexemes_used': [],
                    'error': 'Response too long. Try breaking your query into smaller parts.'
                }
            elif finish_reason not in [1, None]:  # Not STOP or None
                return {
                    'query': '',
                    'explanation': '',
                    'lexemes_used': [],
                    'error': f'Response generation failed (reason: {finish_reason}). Try rephrasing.'
                }
        
        # Try to get the text
        try:
            generated_query = response.text.strip()
        except ValueError as e:
            # response.text accessor failed
            return {
                'query': '',
                'explanation': '',
                'lexemes_used': [],
                'error': 'Could not extract query from response. The prompt may be too complex. Try simplifying.'
            }
        
        # Remove markdown code blocks if present
        if generated_query.startswith('```'):
            lines = generated_query.split('\n')
            # Remove first and last lines if they're code fence markers
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].startswith('```'):
                lines = lines[:-1]
            generated_query = '\n'.join(lines).strip()
        
        # Validate the query
        is_valid, error_msg = validate_query(generated_query)
        
        if not is_valid:
            return {
                'query': generated_query,
                'explanation': 'Query validation failed',
                'lexemes_used': [lex['lex'] for lex in unique_lexemes],
                'error': f'Validation error: {error_msg}'
            }
        
        # Create explanation
        explanation_parts = []
        if unique_lexemes:
            explanation_parts.append("Found lexemes: " + ", ".join(
                f"{lex['gloss']} ({lex['lex']})" for lex in unique_lexemes[:3]
            ))
        explanation_parts.append("Query generated successfully")
        
        return {
            'query': generated_query,
            'explanation': '. '.join(explanation_parts),
            'lexemes_used': [lex['lex'] for lex in unique_lexemes],
            'error': None
        }
        
    except Exception as e:
        return {
            'query': '',
            'explanation': '',
            'lexemes_used': [],
            'error': f'Error generating query: {str(e)}'
        }
