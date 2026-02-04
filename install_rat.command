#!/bin/bash
# RAT Installer Script (Double-clickable)
# Run this once on any Mac to set up the RAT environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "================================================"
echo "  RAT - Rotational/Angular Tracking Installer"
echo "================================================"
echo ""

# Define the absolute path to the conda executable
CONDA_EXE="$HOME/miniconda3/bin/conda"

# 1. Check for conda and install if missing
if [ ! -f "$CONDA_EXE" ]; then
    echo "[!] Conda not found. Installing Miniconda..."
    
    if [[ $(uname -m) == "arm64" ]]; then
        curl -k -L -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
        INSTALLER="Miniconda3-latest-MacOSX-arm64.sh"
    else
        curl -k -L -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
        INSTALLER="Miniconda3-latest-MacOSX-x86_64.sh"
    fi
    
    if [ ! -f "$INSTALLER" ]; then
        echo "Error: Failed to download Miniconda installer."
        read -p "Press any key to exit..."
        exit 1
    fi

    bash "$INSTALLER" -b -p "$HOME/miniconda3"
    rm "$INSTALLER"
    "$CONDA_EXE" init zsh
    echo "[✓] Miniconda installed"
fi

# 2. Configure Conda
"$CONDA_EXE" config --set ssl_verify false

echo ""
echo "[1/3] Creating RAT environment (via conda-forge)..."
# Remove existing env if it exists
"$CONDA_EXE" env remove -n rat -y 2>/dev/null || true

# Create env and install HDF5/PyTables via conda-forge
# This prevents pip from trying to build 'tables' from source (which fails)
"$CONDA_EXE" create -n rat python=3.10 pytables=3.8.0 hdf5 --override-channels -c conda-forge -y

if [ $? -ne 0 ]; then
    echo "CRITICAL ERROR: Failed to create conda environment."
    read -p "Press any key to exit..."
    exit 1
fi

echo ""
echo "[2/3] Installing dependencies..."
RAT_PYTHON="$HOME/miniconda3/envs/rat/bin/python"
RAT_PIP="$HOME/miniconda3/envs/rat/bin/pip"

if [ ! -f "$RAT_PYTHON" ]; then
    echo "Error: Python executable not found at $RAT_PYTHON"
    read -p "Press any key to exit..."
    exit 1
fi

# Upgrade pip first
"$RAT_PIP" install --upgrade pip

# Install dependencies via pip
# Note: We rely on the conda-installed pytables, so we rely on pip detecting it.
"$RAT_PIP" install deeplabcut-live customtkinter opencv-python pandas pillow numpy

# Install full deeplabcut
# It requires tables==3.8.0. Since we installed it via conda, pip should be satisfied.
# If this fails, we will proceed anyway because deeplabcut-live is the critical part for running.
"$RAT_PIP" install deeplabcut || echo "[!] Warning: Full DeepLabCut installation failed (ignoring, as Live is installed)"

echo ""
echo "[3/3] Pre-downloading tracking model (~500MB)..."
"$RAT_PYTHON" -c "from dlclive import DLCLive; DLCLive('superanimal_topviewmouse'); print('[✓] Model ready')" || echo "[!] Model download warning (will retry on first run)"

echo ""
echo "================================================"
echo "  Installation Complete!"
echo "================================================"
echo ""
echo "To run RAT, you can now double-click 'run_rat.command'."
echo ""
read -p "Press any key to close..."
