#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def clean_generated_files():
    """Remove all generated styled SVG and PNG files from the source img directory"""
    img_folder = Path('./img')
    
    if not img_folder.exists():
        print(f"Image folder not found: {img_folder}")
        return
    
    patterns_to_remove = [
        '*_styled.svg',
        '*_styled.png',
        '*_styled_with_context.png',
        'annotation_styled.png',
        'annotation_mri_styled.png',
        'annotation_ct_styled.png',
        'annotatiom_mri_styled.png'
    ]
    
    removed_count = 0
    
    # Find and remove generated files
    for pattern in patterns_to_remove:
        for file_path in img_folder.rglob(pattern):
            try:
                file_path.unlink()
                print(f"Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    print(f"\n✓ Removed {removed_count} generated files from source directories")

if __name__ == "__main__":
    # Ensure we're in the project root
    if not Path('_quarto.yml').exists():
        print("Error: _quarto.yml not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    clean_generated_files()