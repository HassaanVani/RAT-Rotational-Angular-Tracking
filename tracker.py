"""
tracker.py — Vision Engine for RAT
Uses DeepLabCut's pre-trained SuperAnimal-TopViewMouse model.
No training required.
"""
import os
import sys
import numpy as np

# Body part indices for SuperAnimal-TopViewMouse
# Full list: nose, left_ear, right_ear, left_ear_tip, right_ear_tip,
# left_eye, right_eye, neck, mid_back, mouse_center, left_hip, right_hip,
# left_forepaw, left_hindpaw, right_hindpaw, tail_base, tail_1-9, tail_tip
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
        self._load_model()
    
    def _load_model(self):
        """Load the pre-trained SuperAnimal model."""
        try:
            from dlclive import DLCLive
            
            # Load SuperAnimal-TopViewMouse (downloads automatically if needed)
            print("[Tracker] Loading SuperAnimal-TopViewMouse model...")
            self.dlc_live = DLCLive("superanimal_topviewmouse")
            
            # Warm up with a dummy frame
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            self.dlc_live.init_inference(dummy_frame)
            
            self.is_initialized = True
            print("[Tracker] Model loaded successfully!")
            
        except ImportError:
            print("[Tracker] DLC-Live not installed. Running in demo mode.")
            print("[Tracker] To enable tracking: pip install deeplabcut deeplabcut-live")
        except Exception as e:
            print(f"[Tracker] Could not load model: {e}")
            print("[Tracker] Running in demo mode with simulated data.")
    
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
            # Get pose estimation
            pose = self.dlc_live.get_pose(frame)
            
            # pose shape: (num_bodyparts, 3) = [x, y, confidence]
            keypoints = {}
            confidences = {}
            
            for name, idx in PART_INDICES.items():
                x, y, conf = pose[idx]
                
                if conf >= CONFIDENCE_THRESHOLD:
                    keypoints[name] = (int(x), int(y))
                else:
                    # Low confidence fallback
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
