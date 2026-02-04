import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import os
import sys
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import threading
from tracker import Tracker
from classifier import BehaviorClassifier

COLORS = {
    "bg_dark": "#1C1C1E",
    "bg_sidebar": "#2C2C2E",
    "bg_card": "#3A3A3C",
    "text_primary": "#F5F5F7",
    "text_secondary": "#8E8E93",
    "accent": "#5E5CE6",
    "accent_hover": "#7A78E8",
    "zone_top": "#BF5F5F",
    "zone_adj_top": "#BF8F5F",
    "zone_adj_bottom": "#5F8FBF",
    "zone_bottom": "#5F5FBF",
    "arena": "#4CAF50",
    "success": "#32D74B",
    "border": "#48484A",
}

ctk.set_appearance_mode("Dark")

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)


class RATApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.configure(fg_color=COLORS["bg_dark"])
        self.title("RAT — Rotational/Angular Tracking")
        self.geometry("1280x800")
        self.minsize(1000, 700)
        
        try:
            icon_path = get_resource_path("RAT_LOGO.jpg")
            image = Image.open(icon_path)
            icon = ImageTk.PhotoImage(image)
            self.iconphoto(False, icon)
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")

        self.video_path = ""
        self.output_folder = ""
        self.arena_bounds = None
        self.drawing_mode = None
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.zone_rects = []
        self.image_scale = 1.0
        self.image_offset_x = 0
        self.image_offset_y = 0
        self.is_processing = False
        self.current_frame = None
        
        self.tracker = Tracker()
        self.classifier = BehaviorClassifier()
        
        # Preview state
        self.preview_running = False
        self.preview_paused = False
        self.preview_cap = None
        self.preview_frame_idx = 0
        self.preview_total_frames = 0
        self.preview_fps = 30.0

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self, 
            width=280, 
            corner_radius=0, 
            fg_color=COLORS["bg_sidebar"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(0, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)
        
        scroll_content = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        scroll_content.grid(row=0, column=0, sticky="nsew")
        
        title_frame = ctk.CTkFrame(scroll_content, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(24, 8))
        
        ctk.CTkLabel(
            title_frame,
            text="RAT",
            font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Rotational/Angular Tracking",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        
        ctk.CTkFrame(scroll_content, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=16)
        
        self._section_label(scroll_content, "INPUT")
        
        self.btn_load_video = self._sidebar_button(
            scroll_content,
            "Select Video",
            command=self.load_video
        )
        self.lbl_video = ctk.CTkLabel(
            scroll_content, 
            text="No video selected",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=240
        )
        self.lbl_video.pack(anchor="w", padx=24, pady=(0, 8))
        
        self.btn_output = self._sidebar_button(
            scroll_content,
            "Set Output Folder",
            command=self.set_output_folder
        )
        self.lbl_output = ctk.CTkLabel(
            scroll_content, 
            text="No folder selected",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=240
        )
        self.lbl_output.pack(anchor="w", padx=24, pady=(0, 16))
        
        self._section_label(scroll_content, "ARENA CALIBRATION")
        
        self.btn_draw_arena = ctk.CTkButton(
            scroll_content,
            text="Draw Arena",
            height=36,
            fg_color=COLORS["arena"],
            hover_color="#3D8B40",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.start_drawing_arena
        )
        self.btn_draw_arena.pack(fill="x", padx=20, pady=(0, 8))
        
        self.lbl_zone_status = ctk.CTkLabel(
            scroll_content,
            text="Draw the experimental arena",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            justify="left"
        )
        self.lbl_zone_status.pack(anchor="w", padx=24, pady=(4, 16))
        
        self._section_label(scroll_content, "ZONE LEGEND")
        
        zone_legend = ctk.CTkFrame(scroll_content, fg_color="transparent")
        zone_legend.pack(fill="x", padx=20, pady=(0, 16))
        
        zones = [
            ("Top Stimulus", COLORS["zone_top"]),
            ("Adj to Top", COLORS["zone_adj_top"]),
            ("Adj to Bottom", COLORS["zone_adj_bottom"]),
            ("Bottom Stimulus", COLORS["zone_bottom"]),
        ]
        
        for zone_name, zone_color in zones:
            row = ctk.CTkFrame(zone_legend, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkFrame(row, width=12, height=12, fg_color=zone_color, corner_radius=2).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=zone_name, font=ctk.CTkFont(size=10), text_color=COLORS["text_secondary"]).pack(side="left")
        
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color=COLORS["bg_sidebar"])
        bottom_frame.grid(row=1, column=0, sticky="sew", padx=0, pady=0)
        
        ctk.CTkFrame(bottom_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=(0, 12))
        
        # DEBUG PREVIEW SECTION
        self._section_label(bottom_frame, "DEBUG PREVIEW")
        
        preview_controls = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        preview_controls.pack(fill="x", padx=20, pady=(0, 8))
        
        self.btn_preview = ctk.CTkButton(
            preview_controls,
            text="▶ Preview",
            width=100,
            height=32,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=12),
            command=self.toggle_preview
        )
        self.btn_preview.pack(side="left", padx=(0, 4))
        
        self.btn_step = ctk.CTkButton(
            preview_controls,
            text="⏭",
            width=40,
            height=32,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=14),
            command=self.step_preview
        )
        self.btn_step.pack(side="left", padx=(0, 4))
        
        self.btn_stop_preview = ctk.CTkButton(
            preview_controls,
            text="⏹",
            width=40,
            height=32,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=14),
            command=self.stop_preview
        )
        self.btn_stop_preview.pack(side="left")
        
        self.lbl_preview_frame = ctk.CTkLabel(
            bottom_frame,
            text="Frame: 0 / 0",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_secondary"]
        )
        self.lbl_preview_frame.pack(anchor="w", padx=24, pady=(0, 8))
        
        self.lbl_preview_state = ctk.CTkLabel(
            bottom_frame,
            text="State: —",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.lbl_preview_state.pack(anchor="w", padx=24, pady=(0, 12))
        
        ctk.CTkFrame(bottom_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=(0, 12))
        
        self.btn_start = ctk.CTkButton(
            bottom_frame,
            text="▶ Start Processing",
            height=48,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=self.start_processing
        )
        self.btn_start.pack(fill="x", padx=20, pady=(0, 8))
        
        self.progress_bar = ctk.CTkProgressBar(
            bottom_frame,
            height=6,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["accent"]
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 20))
        self.progress_bar.set(0)

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.canvas_container = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=12
        )
        self.canvas_container.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        self.canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas_container.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self.canvas_container,
            bg=COLORS["bg_dark"],
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.status_frame = ctk.CTkFrame(
            self.main_frame,
            height=32,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0
        )
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready — Load a video to begin",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.status_label.pack(side="left", padx=16, pady=6)

    def _section_label(self, parent, text):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=24, pady=(8, 8))

    def _sidebar_button(self, parent, text, command):
        btn = ctk.CTkButton(
            parent,
            text=text,
            height=36,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            font=ctk.CTkFont(size=12),
            anchor="w",
            command=command
        )
        btn.pack(fill="x", padx=20, pady=(0, 4))
        return btn

    def load_video(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Video Files", "*.mp4 *.avi *.mts *.mov *.mkv")]
        )
        if file_path:
            self.video_path = file_path
            self.lbl_video.configure(text=os.path.basename(file_path))
            self.load_first_frame()
            self.status_label.configure(text=f"Loaded: {os.path.basename(file_path)}")
            self._check_ready()

    def set_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_folder = folder_path
            self.lbl_output.configure(text=os.path.basename(folder_path) or folder_path)
            self._check_ready()

    def load_first_frame(self):
        if not self.video_path:
            return
        
        cap = cv2.VideoCapture(self.video_path)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self._display_frame(frame)

    def _display_frame(self, img_array):
        self.update_idletasks()
        h, w, _ = img_array.shape
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        if canvas_w <= 1 or canvas_h <= 1:
            canvas_w, canvas_h = 800, 600
        
        scale = min(canvas_w / w, canvas_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        image = Image.fromarray(img_array)
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, image=self.photo, anchor="center")
        
        self.image_scale = scale
        self.image_offset_x = (canvas_w - new_w) // 2
        self.image_offset_y = (canvas_h - new_h) // 2
        self.current_frame = img_array
        
        if self.arena_bounds:
            self._draw_zone_overlays()

    def start_drawing_arena(self):
        if not self.video_path:
            self.status_label.configure(text="Load a video first")
            return
        self.drawing_mode = "arena"
        self.status_label.configure(text="Draw a rectangle around the experimental arena...")

    def on_mouse_down(self, event):
        if not self.drawing_mode:
            return
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline=COLORS["arena"], width=2
        )

    def on_mouse_drag(self, event):
        if not self.drawing_mode or not self.rect_id:
            return
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        if not self.drawing_mode or not self.rect_id:
            return
        
        end_x, end_y = event.x, event.y
        
        x1 = int((self.start_x - self.image_offset_x) / self.image_scale)
        y1 = int((self.start_y - self.image_offset_y) / self.image_scale)
        x2 = int((end_x - self.image_offset_x) / self.image_scale)
        y2 = int((end_y - self.image_offset_y) / self.image_scale)
        
        self.arena_bounds = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self.classifier.set_arena(self.arena_bounds)
        
        self.btn_draw_arena.configure(text="Arena Set ✓")
        self.lbl_zone_status.configure(text="Arena defined with 4 zones")
        
        self._draw_zone_overlays()
        
        self.drawing_mode = None
        self.status_label.configure(text="Arena configured — Ready to process")
        self._check_ready()

    def _draw_zone_overlays(self):
        for rect in self.zone_rects:
            self.canvas.delete(rect)
        self.zone_rects = []
        
        if not self.arena_bounds:
            return
        
        x1, y1, x2, y2 = self.arena_bounds
        arena_height = y2 - y1
        zone_height = arena_height / 4
        
        zone_colors = [
            COLORS["zone_top"],
            COLORS["zone_adj_top"],
            COLORS["zone_adj_bottom"],
            COLORS["zone_bottom"],
        ]
        
        for i, color in enumerate(zone_colors):
            zy1 = y1 + i * zone_height
            zy2 = y1 + (i + 1) * zone_height
            
            canvas_x1 = x1 * self.image_scale + self.image_offset_x
            canvas_y1 = zy1 * self.image_scale + self.image_offset_y
            canvas_x2 = x2 * self.image_scale + self.image_offset_x
            canvas_y2 = zy2 * self.image_scale + self.image_offset_y
            
            rect = self.canvas.create_rectangle(
                canvas_x1, canvas_y1, canvas_x2, canvas_y2,
                outline=color, width=2, dash=(4, 2)
            )
            self.zone_rects.append(rect)

    def _check_ready(self):
        if self.arena_bounds and self.video_path and self.output_folder:
            self.btn_start.configure(state="normal")
            self.status_label.configure(text="Ready to process")
        else:
            self.btn_start.configure(state="disabled")

    def start_processing(self):
        if self.is_processing:
            return
        self.is_processing = True
        self.btn_start.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)
        
        thread = threading.Thread(target=self._run_analysis, daemon=True)
        thread.start()

    def _run_analysis(self):
        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        results = []
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            keypoints = self.tracker.get_keypoints(frame)
            frame_height = frame.shape[0]
            behavior = self.classifier.classify_full(keypoints, frame_height)
            
            results.append({
                "Frame": frame_idx,
                "Time_s": round(frame_idx / fps, 3),
                "Location": behavior.location,
                "Attention": behavior.attention,
                "Nose_X": keypoints['nose'][0],
                "Nose_Y": keypoints['nose'][1],
                "Head_Angle": behavior.head_angle
            })
            
            frame_idx += 1
            
            if frame_idx % 50 == 0:
                progress = frame_idx / total_frames if total_frames > 0 else 0
                self.after(0, lambda p=progress: self.progress_bar.set(p))
                self.after(0, lambda f=frame_idx: self.status_label.configure(
                    text=f"Processing frame {f}/{total_frames}"
                ))
        
        cap.release()
        
        df = pd.DataFrame(results)
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        save_path = os.path.join(self.output_folder, f"{video_name}_results.csv")
        df.to_csv(save_path, index=False)
        
        self.after(0, lambda: self._on_processing_complete(save_path))

    def _on_processing_complete(self, save_path):
        self.is_processing = False
        self.progress_bar.set(1.0)
        self.btn_start.configure(state="normal", text="Start Processing")
        self.status_label.configure(text=f"Complete — Saved to {os.path.basename(save_path)}")
    
    # --- PREVIEW MODE ---
    def toggle_preview(self):
        """Start or pause preview playback."""
        if not self.video_path:
            self.status_label.configure(text="Load a video first")
            return
        
        if not self.preview_running:
            self._start_preview()
        else:
            self.preview_paused = not self.preview_paused
            if self.preview_paused:
                self.btn_preview.configure(text="▶ Resume")
                self.status_label.configure(text="Preview paused")
            else:
                self.btn_preview.configure(text="⏸ Pause")
                self.status_label.configure(text="Preview running...")
    
    def _start_preview(self):
        """Initialize and start preview playback."""
        self.preview_cap = cv2.VideoCapture(self.video_path)
        self.preview_total_frames = int(self.preview_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.preview_fps = self.preview_cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.preview_frame_idx = 0
        self.preview_running = True
        self.preview_paused = False
        
        self.btn_preview.configure(text="⏸ Pause")
        self.status_label.configure(text="Preview running...")
        
        self._preview_loop()
    
    def _preview_loop(self):
        """Main preview loop - reads and displays frames with overlays."""
        if not self.preview_running:
            return
        
        if not self.preview_paused:
            ret, frame = self.preview_cap.read()
            
            if not ret:
                # End of video, loop back
                self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.preview_frame_idx = 0
                ret, frame = self.preview_cap.read()
            
            if ret:
                self._display_preview_frame(frame)
                self.preview_frame_idx += 1
        
        # Schedule next frame (targeting ~15fps for smooth UI)
        delay = max(16, int(1000 / min(self.preview_fps, 30)))
        self.after(delay, self._preview_loop)
    
    def _display_preview_frame(self, frame):
        """Display a frame with tracking overlays."""
        # Get keypoints
        keypoints = self.tracker.get_keypoints(frame)
        frame_height = frame.shape[0]
        behavior = self.classifier.classify_full(keypoints, frame_height)
        
        # Convert to RGB for display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Draw overlays on the frame
        frame_rgb = self._draw_overlays(frame_rgb, keypoints, behavior)
        
        # Update labels
        self.lbl_preview_frame.configure(
            text=f"Frame: {self.preview_frame_idx} / {self.preview_total_frames}"
        )
        self.lbl_preview_state.configure(text=f"State: {behavior.attention}")
        
        # Display
        self._display_frame(frame_rgb)
    
    def _draw_overlays(self, frame, keypoints, behavior):
        """Draw keypoints, vectors, and zones on the frame."""
        import cv2 as cv
        
        # Colors (BGR format for OpenCV)
        KEYPOINT_COLORS = {
            'nose': (0, 255, 0),       # Green
            'left_ear': (0, 255, 255), # Yellow
            'right_ear': (0, 255, 255),# Yellow
            'tail_base': (0, 0, 255),  # Red
        }
        
        # Draw zone overlays if arena is set
        if self.arena_bounds:
            x1, y1, x2, y2 = self.arena_bounds
            arena_height = y2 - y1
            zone_height = arena_height / 4
            
            zone_colors_bgr = [
                (95, 95, 191),   # zone_top - muted red
                (95, 143, 191),  # zone_adj_top - muted orange
                (191, 143, 95),  # zone_adj_bottom - muted blue
                (191, 95, 95),   # zone_bottom - muted blue
            ]
            
            overlay = frame.copy()
            for i, color in enumerate(zone_colors_bgr):
                zy1 = int(y1 + i * zone_height)
                zy2 = int(y1 + (i + 1) * zone_height)
                cv.rectangle(overlay, (x1, zy1), (x2, zy2), color, -1)
            
            # Blend with original (30% opacity)
            frame = cv.addWeighted(overlay, 0.3, frame, 0.7, 0)
            
            # Draw zone outlines
            for i in range(5):
                zy = int(y1 + i * zone_height)
                cv.line(frame, (x1, zy), (x2, zy), (200, 200, 200), 1)
            cv.rectangle(frame, (x1, y1), (x2, y2), (200, 200, 200), 2)
        
        # Draw keypoints
        for name, color in KEYPOINT_COLORS.items():
            if name in keypoints:
                x, y = keypoints[name]
                cv.circle(frame, (x, y), 6, color, -1)
                cv.circle(frame, (x, y), 8, (255, 255, 255), 1)
        
        # Draw body vector (nose to tail)
        if 'nose' in keypoints and 'tail_base' in keypoints:
            nose = keypoints['nose']
            tail = keypoints['tail_base']
            cv.arrowedLine(frame, tail, nose, (255, 255, 255), 2, tipLength=0.2)
        
        # Draw state label
        label = f"{behavior.attention}"
        label_size = cv.getTextSize(label, cv.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        cv.rectangle(frame, (10, 10), (20 + label_size[0], 35 + label_size[1]), (0, 0, 0), -1)
        cv.putText(frame, label, (15, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def step_preview(self):
        """Step forward one frame in preview."""
        if not self.video_path:
            self.status_label.configure(text="Load a video first")
            return
        
        if not self.preview_cap or not self.preview_cap.isOpened():
            self.preview_cap = cv2.VideoCapture(self.video_path)
            self.preview_total_frames = int(self.preview_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.preview_fps = self.preview_cap.get(cv2.CAP_PROP_FPS) or 30.0
            self.preview_frame_idx = 0
        
        ret, frame = self.preview_cap.read()
        if ret:
            self._display_preview_frame(frame)
            self.preview_frame_idx += 1
        else:
            # Reset to beginning
            self.preview_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.preview_frame_idx = 0
        
        self.status_label.configure(text=f"Frame {self.preview_frame_idx}")
    
    def stop_preview(self):
        """Stop preview and show first frame."""
        self.preview_running = False
        self.preview_paused = False
        
        if self.preview_cap:
            self.preview_cap.release()
            self.preview_cap = None
        
        self.btn_preview.configure(text="▶ Preview")
        self.lbl_preview_frame.configure(text="Frame: 0 / 0")
        self.lbl_preview_state.configure(text="State: —")
        
        if self.video_path:
            self.load_first_frame()
        
        self.status_label.configure(text="Preview stopped")


if __name__ == "__main__":
    app = RATApp()
    app.mainloop()
