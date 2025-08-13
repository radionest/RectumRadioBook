#!/usr/bin/env python3
"""
Setup pandoc-crossref path dynamically based on environment.
This script updates _quarto.yml with the correct path to pandoc-crossref
depending on whether we're running locally or in CI.
"""

import os
import sys
import shutil
import yaml
from pathlib import Path


def find_pandoc_crossref():
    """Find pandoc-crossref executable path."""
    # Check if we're in CI environment
    is_ci = os.environ.get('CI', '').lower() == 'true'
    
    if is_ci:
        # In CI, pandoc-crossref should be in /usr/local/bin
        ci_path = '/usr/local/bin/pandoc-crossref'
        if os.path.exists(ci_path):
            return ci_path
    else:
        # Local environment - check known locations
        local_paths = [
            '/home/nest/.local/bin/quarto_tools/pandoc-crossref',
            '/usr/local/bin/pandoc-crossref',
            shutil.which('pandoc-crossref'),  # Try to find in PATH
        ]
        
        for path in local_paths:
            if path and os.path.exists(path):
                return path
    
    # If not found, try to find it in PATH
    which_path = shutil.which('pandoc-crossref')
    if which_path:
        return which_path
    
    return None


def update_quarto_config(crossref_path):
    """Update _quarto.yml with the correct pandoc-crossref path."""
    config_path = Path('_quarto.yml')
    
    if not config_path.exists():
        print(f"Error: _quarto.yml not found in {os.getcwd()}", file=sys.stderr)
        return False
    
    # Read the config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Update the filters section
    if crossref_path:
        config['filters'] = [crossref_path]
        print(f"Setting pandoc-crossref path to: {crossref_path}")
    else:
        # If no path found, remove the filter (will use Quarto's built-in crossref)
        if 'filters' in config:
            del config['filters']
        print("Warning: pandoc-crossref not found, using Quarto's built-in crossref")
    
    # Write the updated config
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    return True


def main():
    """Main entry point."""
    # Find pandoc-crossref
    crossref_path = find_pandoc_crossref()
    
    if crossref_path:
        print(f"Found pandoc-crossref at: {crossref_path}")
    else:
        print("Warning: pandoc-crossref not found in expected locations")
    
    # Update the config
    if not update_quarto_config(crossref_path):
        sys.exit(1)
    
    print("Successfully updated _quarto.yml")


if __name__ == '__main__':
    main()