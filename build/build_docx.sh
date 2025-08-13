#!/bin/bash

# Build script for converting markdown files to DOCX format
# RectumRadioBook project

# Set variables
OUTPUT_DIR="build"
OUTPUT_FILE="RectumRadioBook.docx"
SRC_DIR="src"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Function to print colored output
print_info() {
    echo -e "\033[0;36m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    print_error "pandoc is not installed. Please install pandoc to use this script."
    exit 1
fi

print_info "Starting conversion to DOCX..."

# List of Quarto markdown files in order
MARKDOWN_FILES=(
    "$SRC_DIR/Introduction.qmd"
    "$SRC_DIR/Rectum-Anatomy.qmd"
    "$SRC_DIR/Scan-Methodology.qmd"
    "$SRC_DIR/Tumor-Detection.qmd"
    "$SRC_DIR/Tumor-Detection/Classification.qmd"
    "$SRC_DIR/Tumor-Detection/MRI.qmd"
    "$SRC_DIR/Tumor-Detection/CT-Detection-Rectal-Cancer.qmd"
    "$SRC_DIR/Rectal-Cancer-Staging.qmd"
    "$SRC_DIR/Rectal-Cancer-Staging/T-Staging.qmd"
    "$SRC_DIR/Rectal-Cancer-Staging/N-Staging.qmd"
    "$SRC_DIR/Rectal-Cancer-Staging/Local-Extent-Assessment.qmd"
    "$SRC_DIR/Rectal-Cancer-Staging/Circumferential-Resection-Margin-Assessment.qmd"
    "$SRC_DIR/Rectal-Cancer-Staging/Extramural-Venous-Invasion-Assessment.qmd"
    "$SRC_DIR/Structured-Report-Primary-MRI-Staging.qmd"
    "$SRC_DIR/Abbrevations.qmd"
    "$SRC_DIR/Bibliography.qmd"
)

# Check if all files exist
print_info "Checking source files..."
for file in "${MARKDOWN_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "File not found: $file"
        exit 1
    fi
done

# Pandoc options
PANDOC_OPTIONS=(
    # Output format
    "-t" "docx"
    # Output file
    "-o" "$OUTPUT_DIR/$OUTPUT_FILE"
    # Standalone document
    "-s"
    # Table of contents
    "--toc"
    # TOC depth
    "--toc-depth=3"
    # Number sections
    "--number-sections"
    # Resource path for images
    "--resource-path=.:img:$SRC_DIR"
    # Citation processing (if bibliography exists)
    "--citeproc"
    # Language
    "-M" "lang=ru"
    # Document metadata
    "-M" "title=Лучевая диагностика рака прямой кишки"
    "-M" "author=RectumRadioBook"
    "-M" "date=$(date +%Y-%m-%d)"
)

# Convert markdown to DOCX
print_info "Converting markdown files to DOCX..."
pandoc "${PANDOC_OPTIONS[@]}" "${MARKDOWN_FILES[@]}" 2>&1 | tee "$OUTPUT_DIR/build.log"

# Check if conversion was successful
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_success "Conversion completed successfully!"
    print_info "Output file: $OUTPUT_DIR/$OUTPUT_FILE"
    
    # Display file size
    if [ -f "$OUTPUT_DIR/$OUTPUT_FILE" ]; then
        FILE_SIZE=$(du -h "$OUTPUT_DIR/$OUTPUT_FILE" | cut -f1)
        print_info "File size: $FILE_SIZE"
    fi
else
    print_error "Conversion failed. Check $OUTPUT_DIR/build.log for details."
    exit 1
fi

print_success "Build process completed!"