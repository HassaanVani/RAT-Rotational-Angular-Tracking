"""
classifier.py — Logic Core for RAT (Rotational/Angular Tracking)
Converts keypoint coordinates to behavioral states per ethogram specification.
"""
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

VELOCITY_THRESHOLD = 5.0
GROOMING_DISTANCE = 50.0
SNIFFING_WALL_DISTANCE = 30.0


@dataclass
class BehaviorResult:
    location: str
    attention: str
    head_angle: float


class BehaviorClassifier:
    def __init__(self):
        self.prev_nose = None
        self.arena_bounds: Optional[Tuple[int, int, int, int]] = None
    
    def set_arena(self, bounds: Tuple[int, int, int, int]):
        self.arena_bounds = bounds
    
    def classify_state(
        self,
        keypoints: Dict,
        zone_a: Optional[Tuple[int, int, int, int]] = None,
        zone_b: Optional[Tuple[int, int, int, int]] = None,
        frame_height: int = 1080
    ) -> str:
        result = self.classify_full(keypoints, frame_height)
        return f"{result.location} | {result.attention}"
    
    def classify_full(
        self,
        keypoints: Dict,
        frame_height: int = 1080
    ) -> BehaviorResult:
        nose = keypoints.get('nose', (0, 0))
        tail = keypoints.get('tail_base', (0, 0))
        left_ear = keypoints.get('left_ear', nose)
        right_ear = keypoints.get('right_ear', nose)
        
        velocity = self._calculate_velocity(nose)
        nose_tail_dist = self._distance(nose, tail)
        head_angle = self._calculate_head_angle(nose, tail)
        
        if self.arena_bounds:
            location = self._get_location_from_arena(nose)
        else:
            location = self._get_location_from_frame(nose, frame_height)
        
        attention = self._get_attention(
            nose, tail, left_ear, right_ear,
            velocity, nose_tail_dist, head_angle, location
        )
        
        return BehaviorResult(
            location=location,
            attention=attention,
            head_angle=head_angle
        )
    
    def _get_location_from_arena(self, nose: Tuple[int, int]) -> str:
        if not self.arena_bounds:
            return "Unknown"
        
        x1, y1, x2, y2 = self.arena_bounds
        arena_height = y2 - y1
        zone_height = arena_height / 4
        
        nose_y = nose[1]
        relative_y = nose_y - y1
        
        if relative_y < 0:
            return "Top Stimulus"
        elif relative_y < zone_height:
            return "Top Stimulus"
        elif relative_y < zone_height * 2:
            return "Adj to Top"
        elif relative_y < zone_height * 3:
            return "Adj to Bottom"
        else:
            return "Bottom Stimulus"
    
    def _get_location_from_frame(self, nose: Tuple[int, int], frame_height: int) -> str:
        zone_height = frame_height / 4
        nose_y = nose[1]
        
        if nose_y < zone_height:
            return "Top Stimulus"
        elif nose_y < zone_height * 2:
            return "Adj to Top"
        elif nose_y < zone_height * 3:
            return "Adj to Bottom"
        else:
            return "Bottom Stimulus"
    
    def _get_attention(
        self,
        nose: Tuple[int, int],
        tail: Tuple[int, int],
        left_ear: Tuple[int, int],
        right_ear: Tuple[int, int],
        velocity: float,
        nose_tail_dist: float,
        head_angle: float,
        location: str
    ) -> str:
        if self._is_grooming(nose_tail_dist, velocity, left_ear, right_ear):
            return "Grooming"
        
        if location == "Top Stimulus" and velocity < VELOCITY_THRESHOLD:
            if self._is_near_arena_edge(nose, "top"):
                return "Sniffing Top"
        
        if location == "Bottom Stimulus" and velocity < VELOCITY_THRESHOLD:
            if self._is_near_arena_edge(nose, "bottom"):
                return "Sniffing Bottom"
        
        return self._get_head_direction(head_angle, nose)
    
    def _is_grooming(
        self,
        nose_tail_dist: float,
        velocity: float,
        left_ear: Tuple[int, int],
        right_ear: Tuple[int, int]
    ) -> bool:
        if nose_tail_dist < GROOMING_DISTANCE and velocity < VELOCITY_THRESHOLD:
            return True
        
        ear_spread = self._distance(left_ear, right_ear)
        if ear_spread < 20 and velocity < VELOCITY_THRESHOLD:
            return True
        
        return False
    
    def _is_near_arena_edge(self, nose: Tuple[int, int], edge: str) -> bool:
        if not self.arena_bounds:
            return True
        
        x1, y1, x2, y2 = self.arena_bounds
        nose_x, nose_y = nose
        
        near_left = abs(nose_x - x1) < SNIFFING_WALL_DISTANCE
        near_right = abs(nose_x - x2) < SNIFFING_WALL_DISTANCE
        
        if edge == "top":
            near_top = abs(nose_y - y1) < SNIFFING_WALL_DISTANCE
            return near_top or near_left or near_right
        else:
            near_bottom = abs(nose_y - y2) < SNIFFING_WALL_DISTANCE
            return near_bottom or near_left or near_right
    
    def _get_head_direction(self, head_angle: float, nose: Tuple[int, int]) -> str:
        if self.arena_bounds:
            x1, y1, x2, y2 = self.arena_bounds
            arena_center_x = (x1 + x2) / 2
            
            if abs(nose[0] - x1) < SNIFFING_WALL_DISTANCE or \
               abs(nose[0] - x2) < SNIFFING_WALL_DISTANCE:
                return "Head Middle/Nothing"
        
        if -45 <= head_angle <= 45:
            return "Head Top"
        elif head_angle > 135 or head_angle < -135:
            return "Head Bottom"
        else:
            return "Head Middle/Nothing"
    
    def _calculate_velocity(self, current_nose: Tuple[int, int]) -> float:
        if self.prev_nose is None:
            self.prev_nose = current_nose
            return 0.0
        
        velocity = self._distance(current_nose, self.prev_nose)
        self.prev_nose = current_nose
        return velocity
    
    def _calculate_head_angle(self, nose: Tuple[int, int], tail: Tuple[int, int]) -> float:
        dx = nose[0] - tail[0]
        dy = tail[1] - nose[1]
        
        angle_rad = np.arctan2(dx, dy)
        angle_deg = np.degrees(angle_rad)
        
        return round(angle_deg, 1)
    
    def _distance(self, p1: Tuple, p2: Tuple) -> float:
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def get_orientation_angle(self, keypoints: Dict) -> float:
        nose = keypoints.get('nose', (0, 0))
        tail = keypoints.get('tail_base', (0, 0))
        return self._calculate_head_angle(nose, tail)
