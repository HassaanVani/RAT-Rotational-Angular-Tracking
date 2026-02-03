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

# --- THEME CONFIGURATION ---
# Muted, professional palette
COLORS = {
    "bg_dark": "#1C1C1E",        # Main background
    "bg_sidebar": "#2C2C2E",     # Sidebar
    "bg_card": "#3A3A3C",        # Cards/panels
    "text_primary": "#F5F5F7",   # Primary text
    "text_secondary": "#8E8E93", # Secondary/muted text
    "accent": "#5E5CE6",         # Primary accent (muted purple)
    "accent_hover": "#7A78E8",   # Accent hover
    "zone_a": "#BF5F5F",         # Muted red for Zone A
    "zone_b": "#5F8FBF",         # Muted blue for Zone B
    "success": "#32D74B",        # Success green
    "border": "#48484A",         # Border color
}

ctk.set_appearance_mode("Dark")

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
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
        
        # Set Icon
        try:
            icon_path = get_resource_path("RAT_LOGO.jpg")
            image = Image.open(icon_path)
            icon = ImageTk.PhotoImage(image)
            self.iconphoto(False, icon)
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")

        # State
        self.video_path = ""
        self.output_folder = ""
        self.zone_a = None
        self.zone_b = None
        self.drawing_mode = None
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None
        self.image_scale = 1.0
        self.image_offset_x = 0
        self.image_offset_y = 0
        self.is_processing = False
        
        self.tracker = Tracker()
        self.classifier = BehaviorClassifier()

        self._build_ui()

    def _build_ui(self):
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(
            self, 
            width=280, 
            corner_radius=0, 
            fg_color=COLORS["bg_sidebar"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Logo/Title
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
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
        
        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=20, pady=16)
        
        # --- Section: Input ---
        self._section_label("INPUT")
        
        self.btn_load_video = self._sidebar_button(
            "Select Video",
            command=self.load_video
        )
        self.lbl_video = ctk.CTkLabel(
            self.sidebar, 
            text="No video selected",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=240
        )
        self.lbl_video.pack(anchor="w", padx=24, pady=(0, 8))
        
        self.btn_output = self._sidebar_button(
            "Set Output Folder",
            command=self.set_output_folder
        )
        self.lbl_output = ctk.CTkLabel(
            self.sidebar, 
            text="No folder selected",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            wraplength=240
        )
        self.lbl_output.pack(anchor="w", padx=24, pady=(0, 16))
        
        # --- Section: Zones ---
        self._section_label("CALIBRATION")
        
        zone_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        zone_frame.pack(fill="x", padx=20, pady=(0, 8))
        
        self.btn_zone_a = ctk.CTkButton(
            zone_frame,
            text="Zone A",
            width=110,
            height=36,
            fg_color=COLORS["zone_a"],
            hover_color="#A04F4F",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.start_drawing('A')
        )
        self.btn_zone_a.pack(side="left", padx=(0, 8))
        
        self.btn_zone_b = ctk.CTkButton(
            zone_frame,
            text="Zone B",
            width=110,
            height=36,
            fg_color=COLORS["zone_b"],
            hover_color="#4F7FAF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.start_drawing('B')
        )
        self.btn_zone_b.pack(side="left")
        
        self.lbl_zone_status = ctk.CTkLabel(
            self.sidebar,
            text="Draw zones on the video frame",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        self.lbl_zone_status.pack(anchor="w", padx=24, pady=(4, 16))
        
        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)
        
        # --- Section: Process ---
        self.btn_start = ctk.CTkButton(
            self.sidebar,
            text="Start Processing",
            height=44,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=self.start_processing
        )
        self.btn_start.pack(fill="x", padx=20, pady=(0, 16))
        
        # Progress
        self.progress_bar = ctk.CTkProgressBar(
            self.sidebar,
            height=4,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["accent"]
        )
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 24))
        self.progress_bar.set(0)

        # --- MAIN CONTENT ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Canvas Container
        self.canvas_container = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=12
        )
        self.canvas_container.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        self.canvas_container.grid_columnconfigure(0, weight=1)
        self.canvas_container.grid_rowconfigure(0, weight=1)

        # Canvas
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
        
        # Status Bar
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

    def _section_label(self, text):
        ctk.CTkLabel(
            self.sidebar,
            text=text,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=24, pady=(8, 8))

    def _sidebar_button(self, text, command):
        btn = ctk.CTkButton(
            self.sidebar,
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

    # --- VIDEO LOADING ---
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

    # --- ZONE DRAWING ---
    def start_drawing(self, zone):
        if not self.video_path:
            self.status_label.configure(text="Load a video first")
            return
        self.drawing_mode = zone
        zone_name = "Zone A (Top Stimulus)" if zone == 'A' else "Zone B (Bottom Stimulus)"
        self.status_label.configure(text=f"Draw {zone_name} on the video...")

    def on_mouse_down(self, event):
        if not self.drawing_mode:
            return
        self.start_x = event.x
        self.start_y = event.y
        color = COLORS["zone_a"] if self.drawing_mode == 'A' else COLORS["zone_b"]
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline=color, width=2
        )

    def on_mouse_drag(self, event):
        if not self.drawing_mode or not self.rect_id:
            return
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        if not self.drawing_mode or not self.rect_id:
            return
        
        end_x, end_y = event.x, event.y
        
        # Map to video coordinates
        x1 = int((self.start_x - self.image_offset_x) / self.image_scale)
        y1 = int((self.start_y - self.image_offset_y) / self.image_scale)
        x2 = int((end_x - self.image_offset_x) / self.image_scale)
        y2 = int((end_y - self.image_offset_y) / self.image_scale)
        
        rect_coords = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

        if self.drawing_mode == 'A':
            self.zone_a = rect_coords
            self.btn_zone_a.configure(text="Zone A ✓")
        else:
            self.zone_b = rect_coords
            self.btn_zone_b.configure(text="Zone B ✓")
        
        self._update_zone_status()
        self.drawing_mode = None
        self._check_ready()

    def _update_zone_status(self):
        parts = []
        if self.zone_a:
            parts.append("Zone A set")
        if self.zone_b:
            parts.append("Zone B set")
        if parts:
            self.lbl_zone_status.configure(text=" · ".join(parts))
            self.status_label.configure(text="Zones configured")
        else:
            self.lbl_zone_status.configure(text="Draw zones on the video frame")

    def _check_ready(self):
        if self.zone_a and self.zone_b and self.video_path and self.output_folder:
            self.btn_start.configure(state="normal")
            self.status_label.configure(text="Ready to process")
        else:
            self.btn_start.configure(state="disabled")

    # --- PROCESSING ---
    def start_processing(self):
        if self.is_processing:
            return
        self.is_processing = True
        self.btn_start.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)
        
        # Run in background thread
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
            state = self.classifier.classify_state(keypoints, self.zone_a, self.zone_b, frame_height)
            
            results.append({
                "Frame": frame_idx,
                "Time_s": round(frame_idx / fps, 3),
                "Location": "Top" if "Top" in state else "Bottom",
                "Behavior": state,
                "Nose_X": keypoints['nose'][0],
                "Nose_Y": keypoints['nose'][1]
            })
            
            frame_idx += 1
            
            # Update progress every 50 frames
            if frame_idx % 50 == 0:
                progress = frame_idx / total_frames if total_frames > 0 else 0
                self.after(0, lambda p=progress: self.progress_bar.set(p))
                self.after(0, lambda f=frame_idx: self.status_label.configure(
                    text=f"Processing frame {f}/{total_frames}"
                ))
        
        cap.release()
        
        # Save CSV
        df = pd.DataFrame(results)
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        save_path = os.path.join(self.output_folder, f"{video_name}_results.csv")
        df.to_csv(save_path, index=False)
        
        # Update UI from main thread
        self.after(0, lambda: self._on_processing_complete(save_path))

    def _on_processing_complete(self, save_path):
        self.is_processing = False
        self.progress_bar.set(1.0)
        self.btn_start.configure(state="normal", text="Start Processing")
        self.status_label.configure(text=f"Complete — Saved to {os.path.basename(save_path)}")

if __name__ == "__main__":
    app = RATApp()
    app.mainloop()
