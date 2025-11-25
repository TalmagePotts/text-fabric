#!/usr/bin/env python3
"""
CORRECT /without/ syntax - the key is matching indentation!
"""

# CORRECT: /without/ has SAME indentation as the atom it quantifies

# Query 1: Nominal clause without preposition after noun
# The n:word is at 2 spaces, so /without/ must also be at 2 spaces
query1_correct = """clause typ=NmCl
  n:word sp=subs
  /without/
    p:word sp=prep
    n :> p
  /-/"""

# Query 2: Verb without noun after it  
# The word is at 0 spaces, so /without/ must be at 0 spaces
query2_correct = """word sp=verb
/without/
  :> word sp=subs
/-/"""

print("=" * 60)
print("CORRECT Query 1 (nominal clause without prep after noun):")
print("=" * 60)
print(query1_correct)
print()

for i, line in enumerate(query1_correct.split('\n'), 1):
    spaces = len(line) - len(line.lstrip(' '))
    print(f"Line {i}: {spaces:2d} spaces | {repr(line)}")

print("\n" + "=" * 60)
print("CORRECT Query 2 (verb without noun after):")
print("=" * 60)
print(query2_correct)
print()

for i, line in enumerate(query2_correct.split('\n'), 1):
    spaces = len(line) - len(line.lstrip(' '))
    print(f"Line {i}: {spaces:2d} spaces | {repr(line)}")
