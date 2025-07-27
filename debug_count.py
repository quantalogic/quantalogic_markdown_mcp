#!/usr/bin/env python3
"""Debug the count issue."""

test_string = """# Main Document

## Chapter 1

##  Chapter 1  

Content with header that has extra spaces.

## Chapter 2

Content for chapter 2.
"""

print("Full content:")
print(repr(test_string))
print("\nLines:")
for i, line in enumerate(test_string.split('\n')):
    print(f"{i}: {repr(line)}")

print(f"\nCount of '## Chapter 1': {test_string.count('## Chapter 1')}")
print(f"Count of '##  Chapter 1': {test_string.count('##  Chapter 1')}")

# Find all occurrences manually
import re
pattern = r'^##.*Chapter 1.*$'
matches = re.findall(pattern, test_string, re.MULTILINE)
print(f"\nRegex matches for header lines: {len(matches)}")
for match in matches:
    print(f"  {repr(match)}")
