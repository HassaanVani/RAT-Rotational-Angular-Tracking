#!/bin/bash
# RAT Launcher - Double-click to run RAT
# This script checks for the conda environment and launches the app

cd "$(dirname "$0")"

# Find conda
if [ -f "$HOME/miniconda3/bin/conda" ]; then
    CONDA_PATH="$HOME/miniconda3"
elif [ -f "$HOME/anaconda3/bin/conda" ]; then
    CONDA_PATH="$HOME/anaconda3"
elif [ -f "/opt/homebrew/Caskroom/miniconda/base/bin/conda" ]; then
    CONDA_PATH="/opt/homebrew/Caskroom/miniconda/base"
else
    osascript -e 'display dialog "Conda not found.\n\nPlease run the Installer first:\n1. Open Terminal\n2. Run: python3 installer.py" buttons {"OK"} default button 1 with title "RAT - Setup Required" with icon caution'
    exit 1
fi

# Check if RAT environment exists
if [ ! -d "$CONDA_PATH/envs/rat" ]; then
    osascript -e 'display dialog "RAT environment not found.\n\nPlease run the Installer first:\n1. Open Terminal\n2. Run: python3 installer.py" buttons {"OK"} default button 1 with title "RAT - Setup Required" with icon caution'
    exit 1
fi

# Activate and run
source "$CONDA_PATH/bin/activate" rat
python main.py
