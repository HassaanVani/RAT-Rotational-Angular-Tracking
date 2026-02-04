# RAT — Rotational/Angular Tracking

**RAT** is an automated behavioral scoring tool for lab mice, designed to replace hours of manual tracking. It uses **DeepLabCut's pre-trained SuperAnimal models** to automatically track mouse keypoints (nose, ears, tail) and classify behaviors like "Sniffing" vs. "Roaming" relative to stimulus zones.

![RAT Logo](RAT_LOGO.jpg)

## Features

- **No Training Required**: Uses the pre-trained `SuperAnimal-TopViewMouse` model (trained on 5,000+ lab mice).
- **Interactive Calibration**: Simply draw "Zone A" (Top) and "Zone B" (Bottom) on the video frame.
- **Automated Scoring**:
  - **Sniffing**: Nose inside zone + mouse stationary.
  - **Head Direction**: Tracks if mouse is facing Top or Bottom half.
  - **Grooming**: Detects when mouse curls up (nose close to tail).
- **Data Export**: Outputs timestamped `.csv` files ready for statistical analysis.

## Quick Start (Mac/Linux)

### 1. Installation (One-Time)
Double-click the `install_rat.sh` script.
- It installs the necessary environment (Miniconda, Python 3.10).
- It downloads the tracking model (~500MB).
- *This takes about 5-10 minutes.*

### 2. Running RAT
Double-click the `run_rat.command` file.
- The interface will open immediately.

---

## Quick Start (Windows)

### Option A: Standalone Executable (Recommended)
Download `RAT.exe` from the [Releases](../../releases) page.
- No installation required — just double-click to run.
- Works on any Windows 10/11 PC.

### Option B: From Source

#### 1. Install Python (One-Time)
Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
> ⚠️ **IMPORTANT**: Check **"Add Python to PATH"** during installation!

#### 2. Install RAT (One-Time)
Double-click `install_rat.bat`
- This creates an isolated environment and downloads dependencies.
- Takes ~5 minutes on first run.

#### 3. Run RAT
Double-click `run_rat.bat`
- The interface opens automatically.
- If not installed, it will install first.

---

## Usage Guide

1. **Load Video**: Click **Select Video** and choose your `.mp4`, `.avi`, or `.mts` file.
2. **Set Output**: Choose where to save the results.
3. **Draw Arena**: Click **Draw Arena** and draw a box around the experimental area.
   - The arena will automatically divide into 4 zones:
     - **Top Stimulus** (top 25%)
     - **Adj to Top** (25-50%)
     - **Adj to Bottom** (50-75%)
     - **Bottom Stimulus** (bottom 25%)
4. **Start Processing**: Click **Start Processing**.
   - The system tracks the mouse frame-by-frame.
   - Status bar shows progress.

## Output Data

The generated `results.csv` contains two behavior tracks:

| Column | Description |
|--------|-------------|
| `Frame` | Video frame number |
| `Time_s` | Timestamp in seconds |
| `Location` | Zone where head is located: `Top Stimulus`, `Adj to Top`, `Adj to Bottom`, `Bottom Stimulus` |
| `Attention` | Behavior state: `Sniffing Top`, `Sniffing Bottom`, `Head Top`, `Head Middle/Nothing`, `Head Bottom`, `Grooming` |
| `Nose_X`, `Nose_Y` | Raw coordinates for custom analysis |
| `Head_Angle` | Orientation angle in degrees |

---

## Developer Info

- **Architecture**: See `VISION.md` for a technical overview.
- **Vision Engine**: DeepLabCut-Live (`tracker.py`).
- **Logic Core**: Geometric rules engine (`classifier.py`).
- **GUI**: CustomTkinter (`main.py`).

### Running from Source
```bash
conda create -n rat python=3.10
conda activate rat
pip install deeplabcut deeplabcut-live customtkinter opencv-python pandas pillow numpy
python main.py
```
