#!/usr/bin/env python3
"""
Test the /without/ quantifier syntax
"""

# Test query 1: Nominal clause without preposition after noun
query1 = """clause typ=NmCl
  n:word sp=subs
/without/
  p:word sp=prep
  n :> p
/-/"""

# Test query 2: Verb without noun after it
query2 = """word sp=verb
/without/
  :> word sp=subs
/-/"""

# Test query 3: Simple example from codebase
query3 = """verse
/without/
  word freq_lex<70
/-/"""

print("Query 1 (nominal clause without prep):")
print(query1)
print("\n" + "="*50 + "\n")

print("Query 2 (verb without noun):")
print(query2)
print("\n" + "="*50 + "\n")

print("Query 3 (verse without rare words):")
print(query3)
print("\n" + "="*50 + "\n")

# Show the exact bytes/spaces
print("Checking indentation of query1:")
for i, line in enumerate(query1.split('\n'), 1):
    spaces = len(line) - len(line.lstrip(' '))
    print(f"Line {i}: {spaces} spaces | {repr(line)}")
