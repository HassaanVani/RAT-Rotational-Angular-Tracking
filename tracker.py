"""
tracker.py — Vision Engine for RAT
Uses DeepLabCut's pre-trained SuperAnimal-TopViewMouse model.
Processes videos using the SuperAnimal inference API.
"""
import os
import numpy as np
import tempfile
import cv2

# Body part indices - SuperAnimal TopViewMouse has specific keypoints
# We need to find: nose, left_ear, right_ear, tail_base
KEYPOINT_NAMES = ['nose', 'left_ear', 'right_ear', 'tail_base']
CONFIDENCE_THRESHOLD = 0.3


class Tracker:
    """
    Vision Engine: Extracts mouse keypoints from video frames.
    Uses DeepLabCut's SuperAnimal-TopViewMouse model.
    
    Note: SuperAnimal models process entire videos, not single frames.
    This class handles the DLC workflow for video analysis.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.error_message = None
        self.superanimal_name = "superanimal_topviewmouse"
        self.keypoint_data = None  # Stores pre-computed keypoints for video
        self.current_video_path = None
        self._check_installation()
    
    def _check_installation(self):
        """Check if DeepLabCut is installed correctly."""
        try:
            import deeplabcut
            print(f"[Tracker] DeepLabCut version: {deeplabcut.__version__}")
            self.is_initialized = True
            self.error_message = None
            print("[Tracker] Ready for video analysis")
        except ImportError as e:
            self.error_message = f"DeepLabCut not installed: {e}"
            print(f"[Tracker] ERROR: {self.error_message}")
        except Exception as e:
            self.error_message = f"Failed to initialize: {e}"
            print(f"[Tracker] ERROR: {self.error_message}")
    
    def analyze_video(self, video_path, progress_callback=None):
        """
        Analyze entire video with SuperAnimal model.
        
        Args:
            video_path: Path to video file
            progress_callback: Optional function(progress) to report progress (0-1)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            print("[Tracker] Not initialized, using demo mode")
            return False
        
        try:
            import deeplabcut
            
            print(f"[Tracker] Analyzing video: {video_path}")
            print("[Tracker] This may take several minutes on first run (downloading model)...")
            
            # Use SuperAnimal inference
            # This creates an H5 file with keypoints next to the video
            deeplabcut.video_inference_superanimal(
                [video_path],
                self.superanimal_name,
                scale_list=[200, 300, 400],  # Multi-scale detection
                video_adapt=True,
                pcutoff=CONFIDENCE_THRESHOLD
            )
            
            # Load the results
            self._load_keypoint_data(video_path)
            self.current_video_path = video_path
            
            print("[Tracker] Video analysis complete!")
            return True
            
        except Exception as e:
            print(f"[Tracker] Analysis failed: {e}")
            self.error_message = str(e)
            return False
    
    def _load_keypoint_data(self, video_path):
        """Load keypoint data from DLC output file."""
        import pandas as pd
        import glob
        
        # DLC creates files like: video_superanimal_topviewmouse.h5
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # Look for the H5 file
        h5_pattern = os.path.join(video_dir, f"{video_name}*superanimal*.h5")
        h5_files = glob.glob(h5_pattern)
        
        if not h5_files:
            print(f"[Tracker] No keypoint file found matching: {h5_pattern}")
            return
        
        h5_path = h5_files[0]
        print(f"[Tracker] Loading keypoints from: {h5_path}")
        
        # Load the H5 file
        self.keypoint_data = pd.read_hdf(h5_path)
        print(f"[Tracker] Loaded {len(self.keypoint_data)} frames of keypoint data")
    
    def get_keypoints(self, frame, frame_idx=None):
        """
        Get keypoints for a specific frame.
        
        Args:
            frame: Video frame (used for fallback/dimensions)
            frame_idx: Frame index if using pre-computed data
            
        Returns:
            dict with 'nose', 'left_ear', 'right_ear', 'tail_base' coordinates
        """
        # If we have pre-computed data, use it
        if self.keypoint_data is not None and frame_idx is not None:
            return self._get_keypoints_from_data(frame_idx, frame)
        
        # Fallback to demo mode
        return self._dummy_keypoints(frame)
    
    def _get_keypoints_from_data(self, frame_idx, frame):
        """Extract keypoints from pre-computed data."""
        if frame_idx >= len(self.keypoint_data):
            return self._dummy_keypoints(frame)
        
        try:
            row = self.keypoint_data.iloc[frame_idx]
            
            # Parse the multi-index columns from DLC output
            # Format: (scorer, bodypart, coord)
            result = {}
            confidences = {}
            
            # Get all column names
            columns = self.keypoint_data.columns
            
            # Find available body parts
            available_parts = set()
            for col in columns:
                if isinstance(col, tuple) and len(col) >= 2:
                    available_parts.add(col[1])
            
            # Map our keypoint names to available parts
            for name in KEYPOINT_NAMES:
                # Try exact match first
                if name in available_parts:
                    x, y, conf = self._get_bodypart_coords(row, columns, name)
                else:
                    # Try alternative names
                    alt_names = {
                        'nose': ['snout', 'nose_tip'],
                        'tail_base': ['tailbase', 'tail_base', 'tail'],
                        'left_ear': ['leftear', 'left_ear', 'ear_left'],
                        'right_ear': ['rightear', 'right_ear', 'ear_right']
                    }
                    found = False
                    for alt in alt_names.get(name, []):
                        if alt in available_parts:
                            x, y, conf = self._get_bodypart_coords(row, columns, alt)
                            found = True
                            break
                    if not found:
                        x, y, conf = frame.shape[1]//2, frame.shape[0]//2, 0.0
                
                if conf >= CONFIDENCE_THRESHOLD:
                    result[name] = (int(x), int(y))
                else:
                    result[name] = (frame.shape[1]//2, frame.shape[0]//2)
                confidences[name] = float(conf)
            
            result['confidence'] = confidences
            return result
            
        except Exception as e:
            print(f"[Tracker] Error parsing keypoints: {e}")
            return self._dummy_keypoints(frame)
    
    def _get_bodypart_coords(self, row, columns, bodypart):
        """Get x, y, confidence for a body part."""
        x, y, conf = 0, 0, 0.0
        
        for col in columns:
            if isinstance(col, tuple) and len(col) >= 2:
                if col[1] == bodypart:
                    if col[2] == 'x':
                        x = row[col]
                    elif col[2] == 'y':
                        y = row[col]
                    elif col[2] == 'likelihood':
                        conf = row[col]
        
        return x, y, conf
    
    def _dummy_keypoints(self, frame=None):
        """Fallback for testing without model."""
        import random
        h, w = (frame.shape[:2] if frame is not None else (720, 1280))
        cx, cy = w // 2, h // 2
        spread = min(w, h) // 4
        
        return {
            'nose': (cx + random.randint(-spread, spread), cy + random.randint(-spread, spread)),
            'left_ear': (cx + random.randint(-spread, spread), cy + random.randint(-spread, spread)),
            'right_ear': (cx + random.randint(-spread, spread), cy + random.randint(-spread, spread)),
            'tail_base': (cx + random.randint(-spread, spread), cy + random.randint(-spread, spread)),
            'confidence': {'nose': 0.0, 'left_ear': 0.0, 'right_ear': 0.0, 'tail_base': 0.0}
        }
