#!/usr/bin/env python3
import os
import sys
import shutil
from lxml import etree
import subprocess
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import styles and functions from prepare_images
from prepare_images import STYLE, nsmap, format_style_xml, get_layer_name

# Output directory from _quarto.yml
OUTPUT_DIR = "_book"

def ensure_output_dir(relative_path):
    """Create output directory structure mirroring source"""
    output_path = Path(OUTPUT_DIR) / relative_path
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

def apply_style_to_file(file_path: str, output_dir: Path):
    """Apply styles to SVG and save to output directory"""
    xml_model = etree.parse(file_path)   
    styled_elements = 0
    
    # Find all path elements
    for path_object in xml_model.findall('.//svg:path',namespaces=nsmap):
        layer_name = get_layer_name(path_object)
        if layer_name and layer_name in STYLE:
            path_object.attrib["style"] = format_style_xml(STYLE[layer_name])
            styled_elements += 1
        else:
            if layer_name:
                print(f"Warning: No style defined for layer '{layer_name}' in {file_path}")
    
    # Also process circles, ellipses, and rects if present
    for shape_type in ['circle', 'ellipse', 'rect']:
        for shape_object in xml_model.findall(f'.//svg:{shape_type}',namespaces=nsmap):
            layer_name = get_layer_name(shape_object)
            if layer_name and layer_name in STYLE:
                shape_object.attrib["style"] = format_style_xml(STYLE[layer_name])
                styled_elements += 1
    
    print(f"Styled {styled_elements} elements in {file_path}")
    
    # Create output filename
    base_name = os.path.basename(file_path).rsplit('.', 1)[0]
    output_filename = f"{base_name}_styled.svg"
    output_filepath = output_dir / output_filename
    
    # Write styled SVG to output directory
    xml_model.write(str(output_filepath), pretty_print=True, xml_declaration=True, encoding='UTF-8')
    return output_filepath

def export_svg_to_png(svg_path: Path, output_dir: Path, dpi=300):
    """Export SVG file to PNG in output directory"""
    inkscape_executable = 'inkscape'
    
    base_name = svg_path.stem
    output_path = output_dir / f'{base_name}.png'
    
    # Export the entire SVG as PNG
    args = [
        inkscape_executable,
        '--export-type=png',
        f'--export-filename={str(output_path.absolute())}',
        f'--export-dpi={dpi}',
        str(svg_path.absolute())
    ]
    
    print(f"Exporting {svg_path} to {output_path}")
    subprocess.call(args)
    return output_path

def copy_original_images(source_dir: Path, output_dir: Path):
    """Copy original images (png, jpg) to output directory"""
    for img_file in source_dir.glob('*.png'):
        if 'styled' not in img_file.name:
            shutil.copy2(img_file, output_dir / img_file.name)
    
    for img_file in source_dir.glob('*.jpg'):
        shutil.copy2(img_file, output_dir / img_file.name)
    
    for img_file in source_dir.glob('*.jpeg'):
        shutil.copy2(img_file, output_dir / img_file.name)

def process_annotation_file(svg_file_path: Path, relative_path: Path):
    """Process a single annotation SVG file and save to output directory"""
    print(f"\nProcessing: {svg_file_path}")
    
    # Create output directory structure
    output_dir = ensure_output_dir(relative_path)
    
    # Copy original images from the same directory
    copy_original_images(svg_file_path.parent, output_dir)
    
    # Apply styles and save to output directory
    styled_svg_path = apply_style_to_file(str(svg_file_path), output_dir)
    
    # Export styled SVG to PNG in output directory
    export_svg_to_png(styled_svg_path, output_dir)
    
    # Also copy the original SVG for reference
    shutil.copy2(svg_file_path, output_dir / svg_file_path.name)

def process_all_annotations():
    """Find and process all annotation SVG files in the project"""
    img_folder = Path('./img')
    annotation_patterns = ['annotation.svg', 'annotation_mri.svg', 'annotation_ct.svg', 'annotatiom_mri.svg']
    
    if not img_folder.exists():
        print(f"Image folder not found: {img_folder}")
        print("Please run this script from the project root directory")
        return
    
    # Process all annotation files
    for svg_file in img_folder.rglob('*.svg'):
        if any(pattern in svg_file.name for pattern in annotation_patterns) and 'styled' not in svg_file.name:
            # Calculate relative path from img folder
            relative_path = svg_file.parent.relative_to(Path('.'))
            try:
                process_annotation_file(svg_file, relative_path)
            except Exception as e:
                print(f"Error processing {svg_file}: {e}")
    
    print(f"\n✓ All processed images saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    # Ensure we're in the project root
    if not Path('_quarto.yml').exists():
        print("Error: _quarto.yml not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    # Process all annotations
    process_all_annotations()