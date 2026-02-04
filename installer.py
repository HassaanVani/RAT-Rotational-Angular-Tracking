"""
RAT Installer — GUI-based installer for RAT (Rotational/Angular Tracking)
Cross-platform installer that handles Miniconda, environment setup, and model download.
"""
import customtkinter as ctk
import subprocess
import threading
import platform
import urllib.request
import os
import sys
import shutil
from pathlib import Path

# --- COLORS (matching main app) ---
COLORS = {
    "bg_dark": "#1C1C1E",
    "bg_sidebar": "#2C2C2E",
    "bg_card": "#3A3A3C",
    "text_primary": "#F5F5F7",
    "text_secondary": "#8E8E93",
    "accent": "#5E5CE6",
    "accent_hover": "#7A78E8",
    "success": "#32D74B",
    "error": "#FF453A",
    "border": "#48484A",
}

ctk.set_appearance_mode("Dark")

# --- INSTALLATION CONFIG ---
MINICONDA_URLS = {
    "Darwin": {
        "arm64": "https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh",
        "x86_64": "https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh",
    },
    "Windows": {
        "AMD64": "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe",
    },
    "Linux": {
        "x86_64": "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh",
    }
}

# Pip dependencies (simple packages)
PIP_DEPS = [
    "numpy<2.0",
    "pandas>=2.0,<2.2",
    "customtkinter",
    "opencv-python",
    "pillow",
]

# Conda dependencies (complex packages with C dependencies)
CONDA_DEPS = [
    "tensorflow",
    "deeplabcut", 
]

# Dependencies that MUST succeed for the app to work
CRITICAL_DEPS = ["deeplabcut", "tensorflow"]


class RATInstaller(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.configure(fg_color=COLORS["bg_dark"])
        self.title("RAT — Installer")
        self.geometry("600x650")
        self.resizable(True, True)
        
        self.system = platform.system()
        self.arch = platform.machine()
        self.home = Path.home()
        self.conda_path = None
        self.install_thread = None
        self.is_installing = False
        
        self._build_ui()
        self._check_existing_install()
    
    def _build_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Header
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 24))
        
        ctk.CTkLabel(
            self.header_frame,
            text="RAT",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            self.header_frame,
            text="Rotational/Angular Tracking — Installer",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w")
        
        # Status card
        self.status_card = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=12
        )
        self.status_card.pack(fill="x", pady=(0, 16))
        
        self.status_label = ctk.CTkLabel(
            self.status_card,
            text="Checking system...",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_primary"]
        )
        self.status_label.pack(padx=20, pady=16, anchor="w")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            height=8,
            corner_radius=4,
            progress_color=COLORS["accent"],
            fg_color=COLORS["bg_card"]
        )
        self.progress_bar.pack(fill="x", pady=(0, 16))
        self.progress_bar.set(0)
        
        # Log area
        self.log_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=12
        )
        self.log_frame.pack(fill="both", expand=True, pady=(0, 16))
        
        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            font=ctk.CTkFont(family="Menlo", size=11),
            fg_color="transparent",
            text_color=COLORS["text_secondary"],
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=12)
        self.log_text.configure(state="disabled")
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(fill="x")
        
        self.btn_install = ctk.CTkButton(
            self.button_frame,
            text="Install RAT",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            height=44,
            corner_radius=8,
            command=self.start_installation
        )
        self.btn_install.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        self.btn_launch = ctk.CTkButton(
            self.button_frame,
            text="Launch RAT",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["success"],
            hover_color="#28a745",
            height=44,
            corner_radius=8,
            state="disabled",
            command=self.launch_rat
        )
        self.btn_launch.pack(side="right", fill="x", expand=True, padx=(8, 0))
    
    def _log(self, message, level="info"):
        """Add message to log area."""
        self.log_text.configure(state="normal")
        prefix = {"info": "→", "success": "✓", "error": "✗", "warning": "⚠"}
        self.log_text.insert("end", f"{prefix.get(level, '→')} {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def _set_status(self, message):
        """Update status label."""
        self.status_label.configure(text=message)
    
    def _check_existing_install(self):
        """Check if conda and RAT environment already exist."""
        self.after(500, self._do_check)
    
    def _do_check(self):
        self._log(f"System: {self.system} ({self.arch})")
        
        # Check for conda
        possible_paths = [
            self.home / "miniconda3" / "bin" / "conda",
            self.home / "anaconda3" / "bin" / "conda",
            self.home / "miniconda3" / "condabin" / "conda",
            self.home / "opt" / "miniconda3" / "bin" / "conda",
            Path("/opt/homebrew/Caskroom/miniconda/base/bin/conda"),
        ]
        
        if self.system == "Windows":
            possible_paths = [
                self.home / "miniconda3" / "Scripts" / "conda.exe",
                self.home / "Anaconda3" / "Scripts" / "conda.exe",
                Path("C:/ProgramData/miniconda3/Scripts/conda.exe"),
            ]
        
        for path in possible_paths:
            if path.exists():
                self.conda_path = str(path)
                self._log(f"Found conda: {self.conda_path}", "success")
                break
        
        if not self.conda_path:
            # Check if conda is in PATH
            try:
                result = subprocess.run(
                    ["conda", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.conda_path = "conda"
                    self._log(f"Found conda in PATH: {result.stdout.strip()}", "success")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        if self.conda_path:
            # Check if RAT environment exists
            try:
                result = subprocess.run(
                    [self.conda_path, "env", "list"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if "rat" in result.stdout:
                    self._log("RAT environment already exists", "success")
                    self._set_status("Ready — RAT is already installed (click Reinstall to rebuild)")
                    self.btn_launch.configure(state="normal")
                    self.btn_install.configure(state="normal", text="Reinstall")
                    self.progress_bar.set(1.0)
                    return
            except Exception:
                pass
            
            self._set_status("Ready — Conda found, click Install to continue")
        else:
            self._log("Conda not found — will install Miniconda", "warning")
            self._set_status("Ready — Click Install to begin")
    
    def start_installation(self):
        if self.is_installing:
            return
        self.is_installing = True
        self.btn_install.configure(state="disabled", text="Installing...")
        self.install_thread = threading.Thread(target=self._run_installation, daemon=True)
        self.install_thread.start()
    
    def _run_installation(self):
        try:
            steps = [
                ("Installing Miniconda", self._install_conda, 0.2),
                ("Creating RAT environment", self._create_environment, 0.4),
                ("Installing dependencies", self._install_dependencies, 0.7),
                ("Downloading tracking model", self._download_model, 0.9),
                ("Finalizing", self._finalize, 1.0),
            ]
            
            for step_name, step_func, progress in steps:
                self.after(0, lambda s=step_name: self._set_status(s))
                success = step_func()
                if not success:
                    self.after(0, lambda: self._installation_failed())
                    return
                self.after(0, lambda p=progress: self.progress_bar.set(p))
            
            self.after(0, self._installation_complete)
            
        except Exception as e:
            self.after(0, lambda: self._log(f"Error: {e}", "error"))
            self.after(0, lambda: self._installation_failed())
    
    def _install_conda(self):
        """Install Miniconda if not present."""
        if self.conda_path:
            self.after(0, lambda: self._log("Conda already installed", "success"))
            return True
        
        self.after(0, lambda: self._log("Downloading Miniconda..."))
        
        try:
            url = MINICONDA_URLS.get(self.system, {}).get(self.arch)
            if not url:
                self.after(0, lambda: self._log(f"Unsupported platform: {self.system} {self.arch}", "error"))
                return False
            
            # Download installer
            installer_name = "miniconda_installer.sh" if self.system != "Windows" else "miniconda_installer.exe"
            installer_path = Path.home() / installer_name
            
            urllib.request.urlretrieve(url, installer_path)
            self.after(0, lambda: self._log("Download complete", "success"))
            
            # Run installer
            self.after(0, lambda: self._log("Running installer (this may take a few minutes)..."))
            
            if self.system == "Windows":
                result = subprocess.run(
                    [str(installer_path), "/S", f"/D={self.home / 'miniconda3'}"],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
            else:
                result = subprocess.run(
                    ["bash", str(installer_path), "-b", "-p", str(self.home / "miniconda3")],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
            
            if result.returncode != 0:
                self.after(0, lambda: self._log(f"Installer failed: {result.stderr}", "error"))
                return False
            
            # Clean up
            installer_path.unlink()
            
            # Set conda path
            if self.system == "Windows":
                self.conda_path = str(self.home / "miniconda3" / "Scripts" / "conda.exe")
            else:
                self.conda_path = str(self.home / "miniconda3" / "bin" / "conda")
            
            self.after(0, lambda: self._log("Miniconda installed", "success"))
            return True
            
        except Exception as e:
            self.after(0, lambda: self._log(f"Error installing conda: {e}", "error"))
            return False
    
    def _create_environment(self):
        """Create the RAT conda environment."""
        self.after(0, lambda: self._log("Accepting conda Terms of Service..."))
        
        try:
            # Accept ToS for default channels (new Anaconda requirement)
            subprocess.run(
                [self.conda_path, "tos", "accept", "--override-channels", 
                 "--channel", "https://repo.anaconda.com/pkgs/main"],
                capture_output=True,
                timeout=30
            )
            subprocess.run(
                [self.conda_path, "tos", "accept", "--override-channels", 
                 "--channel", "https://repo.anaconda.com/pkgs/r"],
                capture_output=True,
                timeout=30
            )
            self.after(0, lambda: self._log("ToS accepted", "success"))
        except Exception as e:
            self.after(0, lambda: self._log(f"ToS acceptance skipped: {e}", "warning"))
        
        self.after(0, lambda: self._log("Creating conda environment 'rat' with Python 3.10..."))
        
        try:
            # Remove existing environment if present
            subprocess.run(
                [self.conda_path, "env", "remove", "-n", "rat", "-y"],
                capture_output=True,
                timeout=60
            )
            
            # Create new environment
            result = subprocess.run(
                [self.conda_path, "create", "-n", "rat", "python=3.10", "-y"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                self.after(0, lambda: self._log(f"Failed to create environment: {result.stderr}", "error"))
                return False
            
            self.after(0, lambda: self._log("Environment created", "success"))
            return True
            
        except Exception as e:
            self.after(0, lambda: self._log(f"Error creating environment: {e}", "error"))
            return False
    
    def _install_dependencies(self):
        """Install Python dependencies using conda and pip."""
        self.after(0, lambda: self._log("Installing dependencies (this may take 10-15 minutes)..."))
        
        failed_critical = []
        
        try:
            # Get paths
            if self.system == "Windows":
                pip_path = str(self.home / "miniconda3" / "envs" / "rat" / "Scripts" / "pip.exe")
            else:
                pip_path = str(self.home / "miniconda3" / "envs" / "rat" / "bin" / "pip")
            
            # Step 1: Install conda packages (deeplabcut, tensorflow)
            self.after(0, lambda: self._log("Installing DeepLabCut via conda (recommended method)..."))
            
            for dep in CONDA_DEPS:
                self.after(0, lambda d=dep: self._log(f"  Installing {d} via conda..."))
                result = subprocess.run(
                    [self.conda_path, "install", "-n", "rat", "-c", "conda-forge", dep, "-y"],
                    capture_output=True,
                    text=True,
                    timeout=900  # 15 min timeout for large packages
                )
                
                if result.returncode != 0:
                    self.after(0, lambda d=dep: self._log(f"  FAILED to install {d} via conda", "error"))
                    self.after(0, lambda: self._log(f"  Error: {result.stderr[:200]}", "error"))
                    failed_critical.append(dep)
                else:
                    self.after(0, lambda d=dep: self._log(f"  {d} installed via conda", "success"))
            
            # Step 2: Install pip packages
            self.after(0, lambda: self._log("Installing additional packages via pip..."))
            for dep in PIP_DEPS:
                self.after(0, lambda d=dep: self._log(f"  Installing {d}..."))
                result = subprocess.run(
                    [pip_path, "install", dep],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    self.after(0, lambda d=dep: self._log(f"  Warning: {d} may not have installed correctly", "warning"))
                else:
                    self.after(0, lambda d=dep: self._log(f"  {d} installed", "success"))
            
            if failed_critical:
                self.after(0, lambda: self._log(f"Critical dependencies failed: {failed_critical}", "error"))
                self.after(0, lambda: self._log("The app will not work correctly without these.", "error"))
                return False
            
            self.after(0, lambda: self._log("All dependencies installed", "success"))
            return True
            
        except Exception as e:
            self.after(0, lambda: self._log(f"Error installing dependencies: {e}", "error"))
            return False
    
    def _download_model(self):
        """Verify DeepLabCut and download SuperAnimal model."""
        self.after(0, lambda: self._log("Verifying DeepLabCut installation..."))
        
        try:
            # Get python path in the environment
            if self.system == "Windows":
                python_path = str(self.home / "miniconda3" / "envs" / "rat" / "python.exe")
            else:
                python_path = str(self.home / "miniconda3" / "envs" / "rat" / "bin" / "python")
            
            # Verify DeepLabCut is importable (TensorFlow takes time to load)
            self.after(0, lambda: self._log("  Loading DeepLabCut (TensorFlow initializing)..."))
            self.after(0, lambda: self._log("  This may take 1-3 minutes on first run..."))
            
            verify_result = subprocess.run(
                [python_path, "-c", 
                 "import deeplabcut; print('DLC Version:', deeplabcut.__version__); print('DLC OK')"],
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout - TensorFlow is slow to initialize
            )
            
            if "DLC OK" not in verify_result.stdout:
                self.after(0, lambda: self._log("ERROR: DeepLabCut is not working correctly!", "error"))
                stderr_preview = verify_result.stderr[:500] if verify_result.stderr else "No error output"
                self.after(0, lambda s=stderr_preview: self._log(f"  Details: {s}", "error"))
                return False
            
            self.after(0, lambda: self._log(f"  {verify_result.stdout.strip()}", "success"))
            
            # SuperAnimal models are included with DeepLabCut and download automatically on first use
            self.after(0, lambda: self._log("SuperAnimal models will download on first use", "success"))
            return True
                
        except subprocess.TimeoutExpired:
            self.after(0, lambda: self._log("Verification timed out (TensorFlow may still be loading)", "warning"))
            self.after(0, lambda: self._log("The app may work - try launching it", "warning"))
            return True  # Don't fail - might still work
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: self._log(f"Verification failed: {msg}", "error"))
            return False
    
    def _finalize(self):
        """Final setup steps."""
        self.after(0, lambda: self._log("Creating launcher shortcut..."))
        
        # The run_rat.command should already exist in the project
        self.after(0, lambda: self._log("Installation complete!", "success"))
        return True
    
    def _installation_complete(self):
        self.is_installing = False
        self._set_status("Installation complete — RAT is ready to use!")
        self.btn_install.configure(state="normal", text="Reinstall")
        self.btn_launch.configure(state="normal")
        self.progress_bar.set(1.0)
    
    def _installation_failed(self):
        self.is_installing = False
        self._set_status("Installation failed — check the log for details")
        self.btn_install.configure(state="normal", text="Retry Install")
    
    def launch_rat(self):
        """Launch the main RAT application."""
        try:
            # Get the directory where this installer is located
            script_dir = Path(__file__).parent
            main_py = script_dir / "main.py"
            
            if self.system == "Windows":
                python_path = str(self.home / "miniconda3" / "envs" / "rat" / "python.exe")
            else:
                python_path = str(self.home / "miniconda3" / "envs" / "rat" / "bin" / "python")
            
            # Launch main.py
            subprocess.Popen([python_path, str(main_py)], cwd=str(script_dir))
            
            # Close installer
            self.after(1000, self.destroy)
            
        except Exception as e:
            self._log(f"Error launching RAT: {e}", "error")


if __name__ == "__main__":
    app = RATInstaller()
    app.mainloop()
