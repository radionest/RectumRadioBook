#!/usr/bin/env python3
import os
import sys
import shutil
from lxml import etree
import subprocess
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import functions from prepare_images and config
from prepare_images import format_style_xml, get_layer_name, load_styles
from config import load_config

# Output directory from _quarto.yml
OUTPUT_DIR = "_book"

def ensure_output_dir(relative_path):
    """Create output directory structure mirroring source"""
    output_path = Path(OUTPUT_DIR) / relative_path
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

def apply_style_to_file(file_path: str, output_dir: Path, styles, nsmap):
    """Apply styles to SVG and save to output directory"""
    xml_model = etree.parse(file_path)   
    styled_elements = 0
    
    # Find all path elements
    for path_object in xml_model.findall('.//svg:path',namespaces=nsmap):
        layer_name = get_layer_name(path_object, nsmap, styles.keys())
        if layer_name and layer_name in styles:
            path_object.attrib["style"] = format_style_xml(styles[layer_name])
            styled_elements += 1
        else:
            if layer_name:
                print(f"Warning: No style defined for layer '{layer_name}' in {file_path}")
    
    # Also process circles, ellipses, and rects if present
    for shape_type in ['circle', 'ellipse', 'rect']:
        for shape_object in xml_model.findall(f'.//svg:{shape_type}',namespaces=nsmap):
            layer_name = get_layer_name(shape_object, nsmap, styles.keys())
            if layer_name and layer_name in styles:
                shape_object.attrib["style"] = format_style_xml(styles[layer_name])
                styled_elements += 1
    
    print(f"Styled {styled_elements} elements in {file_path}")
    
    # Create output filename
    base_name = os.path.basename(file_path).rsplit('.', 1)[0]
    output_filename = f"{base_name}_styled.svg"
    output_filepath = output_dir / output_filename
    
    # Write styled SVG to output directory
    xml_model.write(str(output_filepath), pretty_print=True, xml_declaration=True, encoding='UTF-8')
    return output_filepath

def export_svg_to_png(svg_path: Path, output_dir: Path, inkscape_executable='inkscape', dpi=300, suffix=''):
    """Export SVG file to PNG in output directory"""
    
    base_name = svg_path.stem
    # Add suffix if provided
    if suffix:
        output_filename = f'{base_name}_{suffix}.png'
    else:
        output_filename = f'{base_name}.png'
    output_path = output_dir / output_filename
    
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

def export_svg_element(svg_path: Path, img_id: str, output_filename: str, output_dir: Path,
                      inkscape_executable='inkscape', filetype='png', dpi=300,
                      export_id_only=True, export_with_context=True,
                      suffix='', annotated_suffix=''):
    """Export specific element from SVG by ID to output directory"""
    
    # Build filename with suffixes
    full_suffix = suffix
    if annotated_suffix:
        full_suffix = f"{suffix}_{annotated_suffix}" if suffix else annotated_suffix
    
    # Export only the specified element if requested
    if export_id_only:
        filename = f'{output_filename}_{full_suffix}.{filetype}' if full_suffix else f'{output_filename}.{filetype}'
        output_path = output_dir / filename
        args = [
            inkscape_executable,
            "--export-id-only",
            f"--export-id={img_id}",
            f"--export-type={filetype}",
            f"--export-dpi={dpi}",
            f"--export-filename={str(output_path.absolute())}",
            str(svg_path.absolute()),
        ]
        print(" ".join(args))
        subprocess.call(args)
    
    # Export with surrounding elements (for context) if requested
    if export_with_context:
        filename_context = f'{output_filename}_{annotated_suffix}.{filetype}' if annotated_suffix else f'{output_filename}_with_context.{filetype}'
        output_path_context = output_dir / filename_context
        args = [
            inkscape_executable,
            f"--export-id={img_id}",
            f"--export-type={filetype}",
            f"--export-dpi={dpi}",
            f"--export-filename={str(output_path_context.absolute())}",
            str(svg_path.absolute()),
        ]
        subprocess.call(args)

def svg_to_png_by_images(svg_path: Path, output_dir: Path, nsmap, config):
    """Export each embedded image from SVG to separate PNG files in output directory"""
    xml_model = etree.parse(str(svg_path))
    
    for image_object in xml_model.findall(".//svg:image", namespaces=nsmap):
        # Try to get the original image filename from xlink:href
        href_attr = image_object.attrib.get(f"{{{nsmap['xlink']}}}href", "")
        if href_attr:
            # Extract base filename without extension
            image_name = os.path.splitext(os.path.basename(href_attr))[0]
        else:
            # Fallback to inkscape:label or id
            try:
                image_name = image_object.attrib[f"{{{nsmap['inkscape']}}}label"]
            except KeyError:
                # Use id as last fallback
                image_name = image_object.attrib.get("id", "unnamed")
                print(f"Warning: No xlink:href or inkscape:label for image in {svg_path}, using id: {image_name}")
        
        export_svg_element(
            svg_path,
            image_object.attrib["id"],
            str(image_name),
            output_dir,
            inkscape_executable=config.inkscape.executable,
            filetype=config.inkscape.default_export_format,
            dpi=config.inkscape.default_dpi,
            export_id_only=config.export.export_id_only,
            export_with_context=config.export.export_with_context,
            annotated_suffix=config.processing.annotated_suffix,
        )
        print(f"Exported image: {image_name} (id: {image_object.attrib['id']})")

def copy_annotated_to_source(output_dir: Path, source_dir: Path):
    """Copy generated annotated images back to source directory"""
    for annotated_file in output_dir.glob('*_annotated.png'):
        dest_path = source_dir / annotated_file.name
        shutil.copy2(annotated_file, dest_path)
        print(f"Copied to source: {dest_path}")

def process_annotation_file(svg_file_path: Path, relative_path: Path, config, styles):
    """Process a single annotation SVG file and save to output directory"""
    print(f"\nProcessing: {svg_file_path}")
    
    # Create output directory structure
    output_dir = ensure_output_dir(relative_path)
    
    # Apply styles and save to output directory
    nsmap = config.get_nsmap()
    styled_svg_path = apply_style_to_file(str(svg_file_path), output_dir, styles, nsmap)
    
    # Try to export individual images from the SVG if they exist
    try:
        svg_to_png_by_images(styled_svg_path, output_dir, nsmap, config)
    except Exception as e:
        print(f"No embedded images to export or error: {e}")
        # If no embedded images, export the whole SVG as PNG
        export_svg_to_png(styled_svg_path, output_dir, 
                         inkscape_executable=config.inkscape.executable,
                         dpi=config.inkscape.default_dpi,
                         suffix=config.processing.annotated_suffix)
    
    # Copy generated annotated images back to source directory
    copy_annotated_to_source(output_dir, svg_file_path.parent)
    
    # Also copy the original SVG for reference
    shutil.copy2(svg_file_path, output_dir / svg_file_path.name)

def process_all_annotations(config, styles):
    """Find and process all annotation SVG files in the project"""
    img_folder = Path(config.processing.default_folder)
    annotation_patterns = config.processing.annotation_patterns
    
    if not img_folder.exists():
        print(f"Image folder not found: {img_folder}")
        print("Please run this script from the project root directory")
        return
    
    # Process all annotation files
    for svg_file in img_folder.rglob('*.svg'):
        if any(pattern in svg_file.name for pattern in annotation_patterns) and config.processing.styled_postfix not in svg_file.name:
            # Calculate relative path from img folder
            relative_path = svg_file.parent.relative_to(Path('.'))
            try:
                process_annotation_file(svg_file, relative_path, config, styles)
            except Exception as e:
                print(f"Error processing {svg_file}: {e}")
    
    print(f"\n✓ All processed images saved to {OUTPUT_DIR}/")

if __name__ == "__main__":
    # Ensure we're in the project root
    if not Path('_quarto.yml').exists():
        print("Error: _quarto.yml not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Load configuration and styles
    config = load_config()
    styles = load_styles(config.processing.default_style_file, 
                        default_styles=config.get_default_styles())
    
    # Create output directory if it doesn't exist
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    # Process all annotations
    process_all_annotations(config, styles)