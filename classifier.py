"""
classifier.py — Logic Core for Norvegicus
Converts keypoint coordinates to behavioral states.
"""
import numpy as np
from typing import Dict, Tuple, Optional

# --- THRESHOLDS ---
VELOCITY_THRESHOLD = 5.0   # pixels/frame — below this is "stationary"
GROOMING_DISTANCE = 50.0   # pixels — nose-to-tail distance for grooming


class BehaviorClassifier:
    """
    Logic Core: Determines behavioral state from mouse pose.
    """
    
    def __init__(self):
        self.prev_nose = None
        self.frame_height = None
    
    def classify_state(
        self,
        keypoints: Dict,
        zone_a: Optional[Tuple[int, int, int, int]],
        zone_b: Optional[Tuple[int, int, int, int]],
        frame_height: int = 1080
    ) -> str:
        """
        Classify the current behavioral state.
        
        Args:
            keypoints: Dict from Tracker with 'nose', 'tail_base', etc.
            zone_a: (x1, y1, x2, y2) for Top Stimulus Zone
            zone_b: (x1, y1, x2, y2) for Bottom Stimulus Zone
            frame_height: Height of video frame (for screen-half logic)
            
        Returns:
            str: One of 'Sniffing Top', 'Sniffing Bottom', 'Head Top',
                 'Head Bottom', 'Grooming', or 'Roaming'
        """
        self.frame_height = frame_height
        nose = keypoints.get('nose', (0, 0))
        tail = keypoints.get('tail_base', (0, 0))
        
        # Calculate velocity
        velocity = self._calculate_velocity(nose)
        
        # Calculate nose-tail distance (for grooming detection)
        nose_tail_dist = self._distance(nose, tail)
        
        # --- Grooming Check ---
        if nose_tail_dist < GROOMING_DISTANCE and velocity < VELOCITY_THRESHOLD:
            return "Grooming"
        
        # --- Sniffing Check (in stimulus zones) ---
        if self._point_in_rect(nose, zone_a):
            if velocity < VELOCITY_THRESHOLD:
                return "Sniffing Top"
            else:
                return "Head Top"  # Moving through zone
        
        if self._point_in_rect(nose, zone_b):
            if velocity < VELOCITY_THRESHOLD:
                return "Sniffing Bottom"
            else:
                return "Head Bottom"
        
        # --- Head Direction (screen halves) ---
        midline = frame_height / 2
        nose_y = nose[1]
        
        if nose_y < midline:
            return "Head Top"
        else:
            return "Head Bottom"
    
    def _calculate_velocity(self, current_nose: Tuple[int, int]) -> float:
        """Calculate velocity as distance moved since last frame."""
        if self.prev_nose is None:
            self.prev_nose = current_nose
            return 0.0
        
        velocity = self._distance(current_nose, self.prev_nose)
        self.prev_nose = current_nose
        return velocity
    
    def _distance(self, p1: Tuple, p2: Tuple) -> float:
        """Euclidean distance between two points."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def _point_in_rect(
        self,
        point: Tuple[int, int],
        rect: Optional[Tuple[int, int, int, int]]
    ) -> bool:
        """Check if point is inside rectangle."""
        if rect is None:
            return False
        x, y = point
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def get_orientation_angle(self, keypoints: Dict) -> float:
        """
        Calculate the mouse's body orientation relative to vertical (0°).
        
        Returns:
            float: Angle in degrees (-180 to 180)
            0° = facing up, 90° = facing right, -90° = facing left
        """
        nose = keypoints.get('nose', (0, 0))
        tail = keypoints.get('tail_base', (0, 0))
        
        dx = nose[0] - tail[0]
        dy = tail[1] - nose[1]  # Inverted because Y increases downward
        
        angle_rad = np.arctan2(dx, dy)
        angle_deg = np.degrees(angle_rad)
        
        return round(angle_deg, 1)
