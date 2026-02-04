#!/bin/bash
# Build RAT.app - Creates a Mac application bundle
# This wraps the launcher script in a proper .app

set -e

APP_NAME="RAT"
APP_DIR="dist/${APP_NAME}.app"
CONTENTS="${APP_DIR}/Contents"
MACOS="${CONTENTS}/MacOS"
RESOURCES="${CONTENTS}/Resources"

echo "Building ${APP_NAME}.app..."

# Clean previous build
rm -rf "$APP_DIR"

# Create app structure
mkdir -p "$MACOS"
mkdir -p "$RESOURCES"

# Create launcher script
cat > "${MACOS}/${APP_NAME}" << 'LAUNCHER'
#!/bin/bash
cd "$(dirname "$0")/../../.."

# Find conda
if [ -f "$HOME/miniconda3/bin/conda" ]; then
    CONDA_PATH="$HOME/miniconda3"
elif [ -f "$HOME/anaconda3/bin/conda" ]; then
    CONDA_PATH="$HOME/anaconda3"
elif [ -f "/opt/homebrew/Caskroom/miniconda/base/bin/conda" ]; then
    CONDA_PATH="/opt/homebrew/Caskroom/miniconda/base"
else
    osascript -e 'display dialog "Conda not found.\n\nPlease run the Installer first:\n\npython3 installer.py" buttons {"OK"} default button 1 with title "RAT - Setup Required" with icon caution'
    exit 1
fi

# Check if RAT environment exists
if [ ! -d "$CONDA_PATH/envs/rat" ]; then
    osascript -e 'display dialog "RAT environment not found.\n\nPlease run the Installer first:\n\npython3 installer.py" buttons {"OK"} default button 1 with title "RAT - Setup Required" with icon caution'
    exit 1
fi

# Activate and run
source "$CONDA_PATH/bin/activate" rat
cd "$(dirname "$0")/../../.."
python main.py
LAUNCHER

chmod +x "${MACOS}/${APP_NAME}"

# Create Info.plist
cat > "${CONTENTS}/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>RAT</string>
    <key>CFBundleDisplayName</key>
    <string>RAT - Rotational/Angular Tracking</string>
    <key>CFBundleIdentifier</key>
    <string>com.norvegicus.rat</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleExecutable</key>
    <string>RAT</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# Copy icon if it exists (convert jpg to icns would be needed for proper icon)
if [ -f "RAT_LOGO.jpg" ]; then
    cp RAT_LOGO.jpg "${RESOURCES}/AppIcon.jpg"
fi

echo ""
echo "✓ Built: ${APP_DIR}"
echo ""
echo "To use:"
echo "  1. First run: python3 installer.py (to set up environment)"
echo "  2. Then double-click: dist/RAT.app"
echo ""
echo "To distribute:"
echo "  1. Zip the entire project folder"
echo "  2. Users run installer.py first, then RAT.app"
