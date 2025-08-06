#!/usr/bin/env python3
"""Test script to verify image processing workflow"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ Command failed with return code: {result.returncode}")
    else:
        print("✓ Command completed successfully")
    
    return result.returncode == 0

def main():
    """Test the image processing workflow"""
    # Check if we're in the right directory
    if not Path('_quarto.yml').exists():
        print("Error: _quarto.yml not found. Please run from project root.")
        sys.exit(1)
    
    print("Testing Quarto image processing workflow...")
    
    # Step 1: Clean any existing generated files
    if run_command("python scripts/clean_generated_images.py", 
                   "Clean existing generated files"):
        print("✓ Cleanup successful")
    
    # Step 2: Run pre-render script
    if run_command("python scripts/prepare_images_prerender.py", 
                   "Run pre-render image processing"):
        print("✓ Pre-render processing successful")
        
        # Check if files were created in _book
        book_img_dir = Path('_book/img')
        if book_img_dir.exists():
            styled_files = list(book_img_dir.rglob('*_styled.*'))
            print(f"\n✓ Found {len(styled_files)} styled files in _book/img/")
            for f in styled_files[:5]:  # Show first 5
                print(f"  - {f.relative_to('_book')}")
            if len(styled_files) > 5:
                print(f"  ... and {len(styled_files) - 5} more")
    
    # Step 3: Verify no generated files in source
    img_dir = Path('img')
    source_styled = list(img_dir.rglob('*_styled.*'))
    if source_styled:
        print(f"\n⚠ Warning: Found {len(source_styled)} styled files in source img/")
        for f in source_styled:
            print(f"  - {f}")
    else:
        print("\n✓ No generated files in source img/ directory")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("\nTo run full Quarto build: quarto render")

if __name__ == "__main__":
    main()