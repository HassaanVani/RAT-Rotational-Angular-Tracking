# VISION.md — RAT Project Vision & Architecture

## Purpose

**RAT (Rotational/Angular Tracking)** automates behavioral scoring of laboratory mice from top-down video footage. It replaces 10+ hours of manual clicking with automated batch processing.

### The Problem

Research scientists spend hours manually watching video and clicking to annotate mouse behaviors (e.g., "sniffing stimulus A", "head facing bottom"). Tools like Solomon Coder require frame-by-frame attention, making large-scale studies extremely tedious.

### The Solution

RAT uses computer vision to automatically:
1. Detect the mouse's body pose (nose, ears, tail)
2. Calculate spatial relationships (which zone? which direction?)
3. Classify behaviors based on configurable rules
4. Export timestamped data for statistical analysis

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         RAT System                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   INPUT     │    │   VISION     │    │    LOGIC     │   │
│  │             │───▶│   ENGINE     │───▶│    CORE      │   │
│  │  Video      │    │              │    │              │   │
│  │  Folder     │    │  DeepLabCut  │    │  Classifier  │   │
│  └─────────────┘    │  SuperAnimal │    │  Rules       │   │
│                     └──────────────┘    └──────┬───────┘   │
│                                                 │           │
│  ┌─────────────┐                               │           │
│  │   OUTPUT    │◀──────────────────────────────┘           │
│  │             │                                           │
│  │  CSV Files  │                                           │
│  └─────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | File | Description |
|-----------|------|-------------|
| **GUI** | `main.py` | User interface for video loading, zone calibration, and processing control |
| **Vision Engine** | `tracker.py` | Extracts keypoints using pre-trained SuperAnimal-TopViewMouse model |
| **Logic Core** | `classifier.py` | Converts coordinates to behavioral states using geometric rules |
| **Installer** | `install_rat.sh` | One-click environment setup for new users |
| **Launcher** | `run_rat.command` | Double-click launcher for daily use |

---

## Data Flow

```
Video Frame (BGR)
      │
      ▼
┌─────────────────┐
│  tracker.py     │
│                 │
│  get_keypoints()│──▶ {nose: (x,y), tail_base: (x,y), ...}
└─────────────────┘
      │
      ▼
┌─────────────────┐
│  classifier.py  │
│                 │
│  classify_state()│──▶ "Sniffing Top" | "Head Bottom" | ...
└─────────────────┘
      │
      ▼
┌─────────────────┐
│  pandas         │
│                 │
│  DataFrame      │──▶ results.csv
└─────────────────┘
```

---

## Behavioral States

| State | Detection Logic |
|-------|-----------------|
| `Sniffing Top` | Nose inside Zone A AND velocity < threshold |
| `Sniffing Bottom` | Nose inside Zone B AND velocity < threshold |
| `Head Top` | Nose in upper 50% of frame (not in Zone A) |
| `Head Bottom` | Nose in lower 50% of frame (not in Zone B) |
| `Grooming` | Nose-to-tail distance < threshold AND velocity low |

---

## Technology Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **GUI** | CustomTkinter | Modern dark-mode Python GUI |
| **Vision** | DeepLabCut + SuperAnimal | Pre-trained, no custom training needed |
| **Processing** | OpenCV | Industry standard video handling |
| **Data** | Pandas | Time-series manipulation and CSV export |
| **Distribution** | Conda + Scripts | Reliable cross-machine deployment |

---

## Design Principles

1. **Zero Training Required** — Uses pre-trained models that work out of the box
2. **Minimal User Effort** — Double-click to install, double-click to run
3. **Research-Grade Output** — Timestamped CSV compatible with statistical software
4. **Extensible Rules** — Behavioral logic is isolated in `classifier.py` for easy modification
5. **Offline Capable** — No internet required after initial setup

---

## Future Roadmap

- [ ] Batch processing of entire folders
- [ ] Real-time preview overlay during processing
- [ ] Solomon Coder `.arch` file export (if format is documented)
- [ ] Windows installer scripts
- [ ] GPU acceleration toggle in UI
- [ ] Custom keypoint selection for different experiments

---

## Credits

- **DeepLabCut** — Mathis Lab @ EPFL
- **SuperAnimal Models** — Trained on 5,000+ lab mice
- **Developer** — Norvegicus

---

*Built to save researchers time so they can focus on science, not clicking.*
