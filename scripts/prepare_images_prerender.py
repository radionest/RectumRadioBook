#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup pandoc-crossref path before anything else
from setup_crossref import main as setup_crossref
setup_crossref()

# Import functions from prepare_images
from prepare_images import update_all_annotations, load_styles
from config import load_config

# Output directory from _quarto.yml
OUTPUT_DIR = "_book"

def copy_img_to_book():
    """Copy all files from img/ to _book/img/"""
    source_dir = Path("img")
    dest_dir = Path(OUTPUT_DIR) / "img"
    
    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        return
    
    # Remove existing _book/img if it exists
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    
    # Copy entire img directory to _book
    shutil.copytree(source_dir, dest_dir)
    print(f"✓ Copied {source_dir} to {dest_dir}")
    
    # Count files for reporting
    total_files = sum(1 for _ in dest_dir.rglob("*") if _.is_file())
    print(f"✓ Copied {total_files} files to {dest_dir}")

if __name__ == "__main__":
    # Ensure we're in the project root
    if not Path('_quarto.yml').exists():
        print("Error: _quarto.yml not found. Please run from project root.")
        sys.exit(1)
    
    # Load configuration and styles
    config = load_config()
    styles = load_styles(config.processing.default_style_file, 
                        default_styles=config.get_default_styles())
    
    # First, run image processing to generate annotated files
    img_folder = config.processing.default_folder
    if os.path.exists(img_folder):
        print(f"Processing annotations in {img_folder}...")
        update_all_annotations(img_folder, config, styles)
    else:
        print(f"Warning: Image folder not found: {img_folder}")
    
    # Create output directory if it doesn't exist
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    # Copy all images to _book
    copy_img_to_book()