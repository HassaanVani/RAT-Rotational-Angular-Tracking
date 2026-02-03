#!/bin/bash
# RAT Installer Script
# Run this once on any Mac to set up the RAT environment

echo "================================================"
echo "  RAT - Rotational/Angular Tracking Installer"
echo "================================================"
echo ""

# Check for conda
if ! command -v conda &> /dev/null; then
    echo "[!] Conda not found. Installing Miniconda..."
    
    # Download Miniconda for Mac (ARM or Intel)
    if [[ $(uname -m) == "arm64" ]]; then
        curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
        bash Miniconda3-latest-MacOSX-arm64.sh -b -p $HOME/miniconda3
        rm Miniconda3-latest-MacOSX-arm64.sh
    else
        curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
        bash Miniconda3-latest-MacOSX-x86_64.sh -b -p $HOME/miniconda3
        rm Miniconda3-latest-MacOSX-x86_64.sh
    fi
    
    # Initialize conda
    $HOME/miniconda3/bin/conda init zsh
    source $HOME/.zshrc
    
    echo "[✓] Miniconda installed"
fi

echo ""
echo "[1/3] Creating RAT environment..."
conda create -n rat python=3.10 -y

echo ""
echo "[2/3] Installing dependencies..."
conda activate rat
pip install deeplabcut deeplabcut-live customtkinter opencv-python pandas pillow numpy

echo ""
echo "[3/3] Pre-downloading tracking model (~500MB)..."
python -c "from dlclive import DLCLive; DLCLive('superanimal_topviewmouse'); print('[✓] Model ready')"

echo ""
echo "================================================"
echo "  Installation Complete!"
echo "================================================"
echo ""
echo "To run RAT:"
echo "  1. Open Terminal"
echo "  2. Run: conda activate rat"
echo "  3. Run: python /path/to/RAT/main.py"
echo ""
echo "Or double-click 'run_rat.command' in the RAT folder."
echo ""
