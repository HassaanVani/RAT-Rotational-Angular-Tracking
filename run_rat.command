#!/bin/bash
# Double-click this file to run RAT

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 1. Find and source conda
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh" ]; then
    source "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"
fi

# 2. Try to activate the environment
conda activate rat 2>/dev/null

# 3. Define the python command (use fallback if activate failed)
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    # Try common absolute paths if 'python' isn't in PATH
    if [ -f "$HOME/miniconda3/envs/rat/bin/python" ]; then
        PYTHON_CMD="$HOME/miniconda3/envs/rat/bin/python"
    elif [ -f "$HOME/anaconda3/envs/rat/bin/python" ]; then
        PYTHON_CMD="$HOME/anaconda3/envs/rat/bin/python"
    else
        echo "Error: Could not find 'rat' environment python."
        echo "Please run install_rat.command again."
        read -p "Press any key to fit..."
        exit 1
    fi
fi

# 4. Run the application
"$PYTHON_CMD" "$SCRIPT_DIR/main.py"
