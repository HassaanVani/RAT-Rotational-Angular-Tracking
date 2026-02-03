#!/bin/bash
# Clean previous builds
rm -rf build dist

# Build the executable
# --onefile: bundle everything into a single exe
# --noconsole: don't show the command prompt when running
# --name: the name of the output file
# --hidden-import: ensure customtkinter and others are found if needed (sometimes auto-detected, but good to be safe)
# --add-data: need to add customtkinter's data files manually usually, let's see if pyinstaller handles it now. 
# CustomTkinter usually needs: --add-data "$(python3 -c 'import customtkinter; print(customtkinter.__path__[0])'):customtkinter/"

# Note: PyInstaller creates a .icns automatically from granular image formats on Mac if valid, 
# but for simplicity we pass the jpg and let it try, or it might just appear on the .exe/window.
# For Mac .app bundles, the icon must be in the .app resource structure, which PyInstaller handles with --icon.

python3 -m PyInstaller --noconsole --onefile --name "RAT_Tracker" \
    --icon "RAT_LOGO.jpg" \
    --add-data "RAT_LOGO.jpg:." \
    --add-data "$(python3 -c 'import customtkinter; print(customtkinter.__path__[0])'):customtkinter/" \
    main.py

echo "Build complete. Check the 'dist' folder."
