"""
tracker.py — Vision Engine for RAT
Uses DeepLabCut's pre-trained SuperAnimal-TopViewMouse model.
No training required.
"""
import os
import sys
import numpy as np

# Body part indices for SuperAnimal-TopViewMouse
PART_INDICES = {
    'nose': 0,
    'left_ear': 1,
    'right_ear': 2,
    'tail_base': 15
}

CONFIDENCE_THRESHOLD = 0.5


class Tracker:
    """
    Vision Engine: Extracts mouse keypoints from video frames.
    Uses DeepLabCut's pre-trained SuperAnimal-TopViewMouse model.
    """
    
    def __init__(self):
        self.dlc_live = None
        self.is_initialized = False
        self.error_message = None
        self._load_model()
    
    def _load_model(self):
        """Load the pre-trained SuperAnimal model."""
        try:
            from dlclive import DLCLive
            
            print("[Tracker] Loading SuperAnimal-TopViewMouse model...")
            self.dlc_live = DLCLive("superanimal_topviewmouse")
            
            # Warm up with a dummy frame
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            self.dlc_live.init_inference(dummy_frame)
            
            self.is_initialized = True
            self.error_message = None
            print("[Tracker] Model loaded successfully!")
            
        except ImportError as e:
            self.error_message = "DLC-Live is not installed. Please run the installer."
            print(f"[Tracker] ERROR: {self.error_message}")
            print("[Tracker] Install with: pip install deeplabcut deeplabcut-live")
        except Exception as e:
            self.error_message = f"Failed to load tracking model: {e}"
            print(f"[Tracker] ERROR: {self.error_message}")
    
    def get_keypoints(self, frame):
        """
        Extract keypoints from a video frame.
        
        Args:
            frame: BGR image (numpy array) from OpenCV
            
        Returns:
            dict with 'nose', 'left_ear', 'right_ear', 'tail_base' coordinates
        """
        if not self.is_initialized or self.dlc_live is None:
            return self._dummy_keypoints(frame)
        
        try:
            pose = self.dlc_live.get_pose(frame)
            
            keypoints = {}
            confidences = {}
            
            for name, idx in PART_INDICES.items():
                x, y, conf = pose[idx]
                
                if conf >= CONFIDENCE_THRESHOLD:
                    keypoints[name] = (int(x), int(y))
                else:
                    keypoints[name] = (frame.shape[1] // 2, frame.shape[0] // 2)
                
                confidences[name] = float(conf)
            
            keypoints['confidence'] = confidences
            return keypoints
            
        except Exception as e:
            print(f"[Tracker] Inference error: {e}")
            return self._dummy_keypoints(frame)
    
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
