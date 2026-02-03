# RAT (Rotational/Angular Tracking)

**RAT** is an automated behavioral scoring tool for lab mice, designed to replace manual tracking in research. It uses computer vision to track mouse keypoints and classify behaviors like "Sniffing" and "Head Direction" relative to stimulus zones.

## Features
- **Zone Calibration**: Interactively draw Top (Red) and Bottom (Blue) stimulus zones on the first frame of the video.
- **Automated Tracking**: Tracks Nose, Ears, and Tail Base (Currently simulated for testing).
- **Behavior Classification**: Logic to detect Sniffing vs. Roaming.
- **Data Export**: Generates `results.csv` compatible with analysis workflows.

## Installation (For Developers)

1. **Clone the repository.**
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Requires Python 3.9+*

## Running the App

To run the application directly from source:
```bash
python main.py
```

## Building the Standalone App

To create a double-click application (Mac `.app` or Windows `.exe`) for researchers:

1. **Run the build script:**
   ```bash
   ./build_app.sh
   ```
2. **Find the app:**
   The output will be in the `dist/` folder.
   - On Mac, you will see `RAT_Tracker` (executable).

## Usage Guide
1. **Load Video**: Click "Load Single Video" and select your recording.
2. **Set Zones**:
   - Click "Draw Zone A (Red)" -> Drag a box on the canvas -> Release.
   - Click "Draw Zone B (Blue)" -> Drag a box on the canvas -> Release.
3. **Set Output**: Choose where to save the CSV.
4. **Start Processing**: Click "Start Processing".
5. **Review**: Check the output folder for `results.csv`.
