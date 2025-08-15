#!/usr/bin/env python3
"""
Script to create a mapping between BibTeX keys in references.bib 
and numbered bibliography entries in Bibliography.qmd
"""

import re
import bibtexparser
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize text for better matching"""
    # Remove accents and special characters
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    # Convert to lowercase and remove extra spaces
    text = ' '.join(text.lower().split())
    # Remove punctuation except spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    text = ' '.join(text.split())
    return text


def extract_first_author(authors: str) -> str:
    """Extract first author's last name from author string"""
    # Handle "[и др.]" notation
    authors = authors.split('[и др.]')[0].strip()
    authors = authors.split('et al.')[0].strip()
    # Get first author
    if ',' in authors:
        first_author = authors.split(',')[0].strip()
    elif '.' in authors:
        # Handle cases like "Battersby N. J."
        parts = authors.split()
        if parts:
            first_author = parts[0]
    else:
        first_author = authors.split()[0] if authors else ""
    
    return first_author.lower().strip()


def parse_bibliography_qmd(filepath: Path) -> Dict[int, Dict[str, str]]:
    """Parse Bibliography.qmd to extract numbered entries"""
    entries = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match numbered entries
    # Format: number. authors. title // journal. year. details
    pattern = r'^(\d+)\.\s+(.+?)$'
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        match = re.match(pattern, line, re.MULTILINE)
        if match:
            num = int(match.group(1))
            full_text = match.group(2)
            
            # Split by '//' to separate authors/title from journal info
            parts = full_text.split('//')
            if len(parts) >= 2:
                # First part contains authors and title
                first_part = parts[0].strip()
                
                # Try to identify where authors end and title begins
                # Authors usually end with a period followed by a capital letter or quote
                author_title_match = re.match(r'^(.+?)\.\s+([A-ZА-Я«"].+)', first_part)
                if author_title_match:
                    authors = author_title_match.group(1).strip()
                    title = author_title_match.group(2).strip()
                else:
                    # Fallback: assume first sentence is authors
                    sentences = first_part.split('. ')
                    authors = sentences[0].strip() if sentences else ""
                    title = '. '.join(sentences[1:]).strip() if len(sentences) > 1 else first_part
            else:
                # No '//' separator, try to parse differently
                sentences = full_text.split('. ')
                authors = sentences[0].strip() if sentences else ""
                title = '. '.join(sentences[1:]).strip() if len(sentences) > 1 else ""
            
            entries[num] = {
                'authors': authors,
                'title': title,
                'full_text': full_text
            }
    
    return entries


def parse_bibtex(filepath: Path) -> Dict[str, Dict[str, str]]:
    """Parse references.bib to extract BibTeX entries"""
    with open(filepath, 'r', encoding='utf-8') as f:
        bib_database = bibtexparser.load(f)
    
    entries = {}
    for entry in bib_database.entries:
        key = entry.get('ID', '')
        if not key:
            continue
            
        # Extract authors
        authors_raw = entry.get('author', '')
        if authors_raw:
            # Parse BibTeX author format
            authors_list = []
            for author in authors_raw.split(' and '):
                author = author.strip()
                # Handle different author formats
                if ',' in author:
                    # Format: "Last, First"
                    parts = author.split(',')
                    last_name = parts[0].strip()
                else:
                    # Format: "First Last" or just "Last"
                    parts = author.split()
                    if parts:
                        # Assume last part is last name
                        last_name = parts[-1].strip()
                    else:
                        last_name = author
                
                # Clean up brackets and special characters
                last_name = re.sub(r'[{}]', '', last_name)
                authors_list.append(last_name)
            
            authors = ', '.join(authors_list)
        else:
            authors = ""
        
        # Extract title
        title = entry.get('title', '')
        # Clean up BibTeX formatting
        title = re.sub(r'[{}]', '', title)
        title = title.replace('{{', '').replace('}}', '')
        
        entries[key] = {
            'authors': authors,
            'title': title,
            'first_author': extract_first_author(authors),
            'normalized_title': normalize_text(title)
        }
    
    return entries


def match_entries(bib_entries: Dict[int, Dict], bibtex_entries: Dict[str, Dict]) -> List[Tuple]:
    """Match bibliography entries with BibTeX keys"""
    matches = []
    
    for num, bib_entry in bib_entries.items():
        best_match = None
        best_score = 0
        
        bib_first_author = extract_first_author(bib_entry['authors'])
        bib_title_normalized = normalize_text(bib_entry['title'])
        
        for key, bibtex_entry in bibtex_entries.items():
            score = 0
            
            # Check author match
            bibtex_first_author = bibtex_entry['first_author']
            if bib_first_author and bibtex_first_author:
                if bib_first_author in bibtex_first_author or bibtex_first_author in bib_first_author:
                    score += 50
            
            # Check title match
            if bib_title_normalized and bibtex_entry['normalized_title']:
                # Calculate similarity based on common words
                bib_words = set(bib_title_normalized.split())
                bibtex_words = set(bibtex_entry['normalized_title'].split())
                
                if bib_words and bibtex_words:
                    intersection = bib_words & bibtex_words
                    union = bib_words | bibtex_words
                    if union:
                        similarity = len(intersection) / len(union)
                        score += similarity * 50
                
                # Bonus for exact substring match
                if bib_title_normalized[:30] in bibtex_entry['normalized_title'] or \
                   bibtex_entry['normalized_title'][:30] in bib_title_normalized:
                    score += 20
            
            if score > best_score:
                best_score = score
                best_match = key
        
        if best_match and best_score > 30:  # Threshold for accepting a match
            matches.append((
                num,
                best_match,
                bib_entry['title'][:80] + ('...' if len(bib_entry['title']) > 80 else ''),
                bib_entry['authors'][:50] + ('...' if len(bib_entry['authors']) > 50 else '')
            ))
        else:
            # No match found
            matches.append((
                num,
                '',
                bib_entry['title'][:80] + ('...' if len(bib_entry['title']) > 80 else ''),
                bib_entry['authors'][:50] + ('...' if len(bib_entry['authors']) > 50 else '')
            ))
    
    return matches


def create_mapping_file(matches: List[Tuple], output_path: Path):
    """Create the bibliography-mapping.md file"""
    content = ["# Bibliography Mapping\n"]
    content.append("| Number | Pandoc Key | Title | Authors |")
    content.append("|--------|------------|-------|---------|")
    
    # Sort by number
    matches.sort(key=lambda x: x[0])
    
    for num, key, title, authors in matches:
        pandoc_key = f"@{key}" if key else "NOT FOUND"
        content.append(f"| {num} | {pandoc_key} | {title} | {authors} |")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))


def main():
    # Define file paths
    base_dir = Path('/home/nest/Documents/RectumRadioBook')
    bib_qmd_path = base_dir / 'src' / 'Bibliography.qmd'
    bibtex_path = base_dir / 'references.bib'
    output_path = base_dir / 'bibliography-mapping.md'
    
    print("Parsing Bibliography.qmd...")
    bib_entries = parse_bibliography_qmd(bib_qmd_path)
    print(f"Found {len(bib_entries)} numbered entries")
    
    print("\nParsing references.bib...")
    bibtex_entries = parse_bibtex(bibtex_path)
    print(f"Found {len(bibtex_entries)} BibTeX entries")
    
    print("\nMatching entries...")
    matches = match_entries(bib_entries, bibtex_entries)
    
    print("\nCreating mapping file...")
    create_mapping_file(matches, output_path)
    
    print(f"\nMapping file created: {output_path}")
    
    # Print summary
    matched = sum(1 for m in matches if m[1])
    unmatched = len(matches) - matched
    print(f"\nSummary:")
    print(f"  Total entries: {len(matches)}")
    print(f"  Matched: {matched}")
    print(f"  Unmatched: {unmatched}")


if __name__ == "__main__":
    main()