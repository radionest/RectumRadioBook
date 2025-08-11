import os
from lxml import etree
import subprocess
import re
from pathlib import Path

nsmap = {
    'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
    'cc': 'http://web.resource.org/cc/',
    'svg': 'http://www.w3.org/2000/svg',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'xlink': 'http://www.w3.org/1999/xlink',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape'
    }


def parse_css_file(css_path):
    """Parse CSS file and extract styles into a dictionary"""
    styles = {}
    
    if not os.path.exists(css_path):
        print(f"Warning: CSS file not found at {css_path}")
        return styles
    
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Remove comments
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # Pattern to match CSS rules
    pattern = r'\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\{([^}]+)\}'
    
    for match in re.finditer(pattern, css_content):
        class_name = match.group(1)
        properties = match.group(2)
        
        style_dict = {}
        
        # Parse individual properties
        for prop_match in re.finditer(r'([a-zA-Z-]+)\s*:\s*([^;]+);?', properties):
            prop_name = prop_match.group(1).strip()
            prop_value = prop_match.group(2).strip()
            
            # Handle stroke-dasharray special case
            if prop_name == 'stroke-dasharray':
                # Convert "1,1" to [1,1]
                values = prop_value.split(',')
                try:
                    style_dict[prop_name] = [float(v.strip()) for v in values]
                except ValueError:
                    style_dict[prop_name] = prop_value
            # Handle numeric properties
            elif prop_name in ['stroke-opacity', 'fill-opacity', 'stroke-dashoffset']:
                try:
                    style_dict[prop_name] = float(prop_value)
                except ValueError:
                    style_dict[prop_name] = prop_value
            else:
                style_dict[prop_name] = prop_value
        
        # Map class names to the expected format
        # Convert layer_1 to 'Слой 1' for backward compatibility
        if class_name == 'layer_1':
            styles['Слой 1'] = style_dict
        else:
            styles[class_name] = style_dict
    
    return styles


def load_styles(style_file='annotation.css'):
    """Load styles from CSS file in styles directory"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    css_path = project_root / 'styles' / style_file
    
    styles = parse_css_file(css_path)
    
    if not styles:
        print(f"Warning: No styles loaded from {css_path}, using default styles")
        # Fallback to default styles
        return {
            'mucosa': {"fill":"#ffe5b4", "stroke":"none", "stroke-opacity":1, "stroke-width":'0.7%'},
            'Слой 1': {"fill":"none", "stroke":"#000000", "stroke-opacity":1, "stroke-width":'0.5%'}
        }
    
    return styles


# Load styles from CSS file
STYLE = load_styles()

def format_style_xml(style_dict):
    output_string = ""
    for style_name, style_value in style_dict.items():
        if isinstance(style_value, list):
            output_string+=f"{style_name}:{','.join(map(str,style_value))};"
        else:
            output_string+=f"{style_name}:{str(style_value)};"
    return output_string

    

def get_layer_name(element):
    """Extract layer name from parent group or use element's inkscape:label"""
    # Try to get layer name from parent group
    parent = element.getparent()
    if parent is not None and f"{{{nsmap['inkscape']}}}label" in parent.attrib:
        return parent.attrib[f"{{{nsmap['inkscape']}}}label"]
    # Try to get from element itself
    if f"{{{nsmap['inkscape']}}}label" in element.attrib:
        return element.attrib[f"{{{nsmap['inkscape']}}}label"]
    # Try id attribute as fallback
    if 'id' in element.attrib:
        # Extract layer name from id if it matches our naming convention
        element_id = element.attrib['id']
        for layer_name in STYLE.keys():
            if layer_name in element_id:
                return layer_name
    return None

def apply_style_to_file(file_path: str, output_postfix='styled'):
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
    
    # Create output path with absolute path
    file_path = os.path.abspath(file_path)
    base_name = os.path.basename(file_path).rsplit('.', 1)[0]
    output_filename = f"{base_name}_{output_postfix}.svg"
    output_filepath = os.path.join(os.path.dirname(file_path), output_filename)
    
    # Write styled SVG
    xml_model.write(output_filepath, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    return output_filepath
    

def export_svg_to_png(file_path, output_filename=None, dpi=300):
    """Export SVG file to PNG using Inkscape"""
    inkscape_executable = 'inkscape'  # Use system inkscape
    
    # Ensure absolute path
    file_path = os.path.abspath(file_path)
    
    if output_filename is None:
        base_name = os.path.basename(file_path).rsplit('.', 1)[0]
        output_filename = base_name
    
    output_dir = os.path.dirname(file_path)
    output_path = os.path.join(output_dir, f'{output_filename}.png')
    
    # Export the entire SVG as PNG
    args = [
        inkscape_executable,
        '--export-type=png',
        f'--export-filename={output_path}',
        f'--export-dpi={dpi}',
        file_path
    ]
    
    print(f"Exporting {file_path} to {output_path}")
    subprocess.call(args)
    

def export_svg_element(file_path, img_id, output_filename, filetype='png', dpi=300):
    """Export specific element from SVG by ID"""
    inkscape_executable = 'inkscape'
    
    # Ensure absolute path
    file_path = os.path.abspath(file_path)
    output_path = os.path.dirname(file_path)

    # Export only the specified element
    args=[
        inkscape_executable,
        '--export-id-only',
        f'--export-id={img_id}',
        f'--export-type={filetype}',
        f'--export-dpi={dpi}',
        f'--export-filename={os.path.join(output_path, f"{output_filename}.{filetype}")}',
        file_path
    ]
    print(' '.join(args))
    subprocess.call(args)

    # Export with surrounding elements (for context)
    args=[
        inkscape_executable,
        f'--export-id={img_id}',
        f'--export-type={filetype}',
        f'--export-dpi={dpi}',
        f'--export-filename={os.path.join(output_path, f"{output_filename}_with_context.{filetype}")}',
        file_path
    ]
    subprocess.call(args)


def svg_to_png_by_images(file_path):
    """Export each embedded image from SVG to separate PNG"""
    xml_model = etree.parse(file_path)   
    for image_object in xml_model.findall('.//svg:image',namespaces=nsmap):
        try:
            image_name = image_object.attrib[f"{{{nsmap['inkscape']}}}label"]
        except KeyError:
            # Use id as fallback
            image_name = image_object.attrib.get('id', 'unnamed')
            print(f"Warning: No inkscape:label for image in {file_path}, using id: {image_name}")
        
        export_svg_element(file_path, image_object.attrib['id'], str(image_name))
        print(f"Exported image: {image_object.attrib['id']}")


def process_annotation_file(svg_file_path):
    """Process a single annotation SVG file: apply styles and export to PNG"""
    print(f"\nProcessing: {svg_file_path}")
    
    # Apply styles
    styled_svg_path = apply_style_to_file(svg_file_path, 'styled')
    
    # Export styled SVG to PNG
    export_svg_to_png(styled_svg_path)
    
    # If the SVG contains embedded images, export them separately
    try:
        svg_to_png_by_images(styled_svg_path)
    except Exception as e:
        print(f"No embedded images to export or error: {e}")


def update_all_annotations(base_folder):
    """Find and process all annotation SVG files in the project"""
    annotation_patterns = ['annotation.svg', 'annotation_mri.svg', 'annotation_ct.svg', 'annotatiom_mri.svg']
    
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if any(pattern in file for pattern in annotation_patterns) and 'styled' not in file:
                file_path = os.path.join(root, file)
                try:
                    process_annotation_file(file_path)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Apply styles to SVG annotation files')
    parser.add_argument('--style', default='annotation.css', 
                        help='CSS file name in styles directory (default: annotation.css)')
    parser.add_argument('--folder', default='./img', 
                        help='Folder to process (default: ./img)')
    args = parser.parse_args()
    
    # Load specified style file
    STYLE = load_styles(args.style)
    
    # Process all annotation files in the specified directory
    img_folder = args.folder
    
    if os.path.exists(img_folder):
        print(f"Using styles from: styles/{args.style}")
        print(f"Processing folder: {img_folder}")
        update_all_annotations(img_folder)
    else:
        print(f"Image folder not found: {img_folder}")
        print("Please run this script from the project root directory")