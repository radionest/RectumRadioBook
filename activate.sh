#!/bin/bash
# Convenience script to activate virtual environment

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "Installing/updating dependencies..."
    pip install -r requirements.txt
fi

echo "Virtual environment activated. To deactivate, run: deactivate"