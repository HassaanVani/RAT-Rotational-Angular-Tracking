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

## Usage Guide

1. **Load Video**: Click **Select Video** and choose your `.mp4`, `.avi`, or `.mts` file.
2. **Set Output**: Choose where to save the results.
3. **Calibrate Zones**:
   - Click **Zone A** (Red) → Draw a box around the Top Stimulus.
   - Click **Zone B** (Blue) → Draw a box around the Bottom Stimulus.
4. **Start Processing**: Click **Start Processing**.
   - The system tracks the mouse frame-by-frame.
   - Status bar shows progress.

## Output Data

The generated `results.csv` contains:
- `Frame`: Video frame number.
- `Time_s`: Timestamp in seconds.
- `Location`: "Top" or "Bottom" (based on screen half).
- `Behavior`: Specific state (e.g., `Sniffing Top`, `Grooming`, `Head Bottom`).
- `Nose_X`, `Nose_Y`: Raw coordinates for custom analysis.

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
