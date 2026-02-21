import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import os
import json
from threading import Thread
import queue
import webbrowser
import time
import re

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Pro")
        self.root.geometry("1000x750")
        
        # Data structures
        self.playlist_videos = []
        self.selected_videos = set()
        self.download_queue = queue.Queue()
        self.is_downloading = False
        self.custom_folder_path = ""
        self.available_formats = []
        self.fetch_in_progress = False
        
        self.setup_ui()
        self.check_all_dependencies()
        
    def setup_ui(self):
        """Setup the main UI elements"""
        # Title
        title_label = ttk.Label(self.root, text="🎥 YouTube Downloader Pro", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # URL Input Frame
        url_frame = ttk.LabelFrame(self.root, text="Enter YouTube URL", padding=10)
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=70, font=('Arial', 10))
        url_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        self.fetch_btn = ttk.Button(url_frame, text="🔍 Fetch Content", command=self.fetch_content)
        self.fetch_btn.pack(side=tk.LEFT)
        
        # Loading indicator for fetch
        self.fetch_loading = ttk.Label(url_frame, text="", font=('Arial', 10))
        self.fetch_loading.pack(side=tk.LEFT, padx=10)
        
        # Folder Options Frame
        folder_frame = ttk.LabelFrame(self.root, text="📁 Folder Options", padding=10)
        folder_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Auto-create folder checkbox
        self.auto_folder_var = tk.BooleanVar(value=True)
        self.auto_folder_check = ttk.Checkbutton(
            folder_frame, 
            text="Auto-create folder from playlist/video title", 
            variable=self.auto_folder_var,
            command=self.toggle_folder_entry
        )
        self.auto_folder_check.pack(anchor=tk.W)
        
        # Custom folder frame
        self.custom_folder_frame = ttk.Frame(folder_frame)
        self.custom_folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.custom_folder_frame, text="Custom folder:").pack(side=tk.LEFT, padx=(20, 5))
        self.folder_path_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.folder_entry = ttk.Entry(self.custom_folder_frame, textvariable=self.folder_path_var, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(self.custom_folder_frame, text="📂 Browse", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        
        # Download Options Frame
        options_frame = ttk.LabelFrame(self.root, text="⚙️ Download Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Format selection
        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(format_frame, text="Format:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.format_var = tk.StringVar(value="mp4")
        
        formats = [
            ("🎬 MP4 Video", "mp4"),
            ("🎬 WebM Video", "webm"),
            ("🎵 MP3 Audio", "mp3"),
            ("⭐ Best Quality", "best")
        ]
        
        for text, value in formats:
            ttk.Radiobutton(
                format_frame, 
                text=text, 
                variable=self.format_var, 
                value=value,
                command=self.update_quality_options
            ).pack(side=tk.LEFT, padx=10)
        
        # Quality selection (for video formats)
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quality_frame, text="Quality:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.quality_var = tk.StringVar(value="720p")
        self.quality_combo = ttk.Combobox(
            quality_frame, 
            textvariable=self.quality_var,
            values=["2160p (4K)", "1440p (2K)", "1080p", "720p", "480p", "360p", "240p"],
            state="readonly",
            width=20
        )
        self.quality_combo.pack(side=tk.LEFT, padx=5)
        self.quality_combo.set("720p")
        
        # Additional options
        extra_frame = ttk.Frame(options_frame)
        extra_frame.pack(fill=tk.X, pady=5)
        
        self.subtitles_var = tk.BooleanVar()
        ttk.Checkbutton(extra_frame, text="Download subtitles", variable=self.subtitles_var).pack(side=tk.LEFT, padx=20)
        
        self.thumbnail_var = tk.BooleanVar()
        ttk.Checkbutton(extra_frame, text="Download thumbnail", variable=self.thumbnail_var).pack(side=tk.LEFT, padx=20)
        
        # Content Display Frame
        content_frame = ttk.LabelFrame(self.root, text="📋 Available Content", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for displaying videos
        columns = ("selected", "index", "title", "duration", "quality", "size")
        self.tree = ttk.Treeview(content_frame, columns=columns, show="headings", height=12)
        
        # Define headings
        self.tree.heading("selected", text="✓")
        self.tree.heading("index", text="#")
        self.tree.heading("title", text="Video Title")
        self.tree.heading("duration", text="Duration")
        self.tree.heading("quality", text="Available Qualities")
        self.tree.heading("size", text="Est. Size")
        
        # Define columns
        self.tree.column("selected", width=40, anchor=tk.CENTER)
        self.tree.column("index", width=50, anchor=tk.CENTER)
        self.tree.column("title", width=450)
        self.tree.column("duration", width=80, anchor=tk.CENTER)
        self.tree.column("quality", width=200)
        self.tree.column("size", width=100, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind click event for checkbox toggling
        self.tree.bind("<Button-1>", self.on_tree_click)
        
        # Control Frame
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Left side buttons
        left_buttons = ttk.Frame(control_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(left_buttons, text="✅ Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_buttons, text="❌ Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        
        # Right side buttons
        right_buttons = ttk.Frame(control_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        self.download_btn = ttk.Button(right_buttons, text="📥 Download Selected", command=self.start_download, style='Accent.TButton')
        self.download_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(right_buttons, text="🔄 Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(self.root, text="📊 Download Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var, font=('Arial', 10)).pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Current download info
        self.current_download_var = tk.StringVar(value="")
        ttk.Label(progress_frame, textvariable=self.current_download_var, font=('Arial', 9)).pack()
        
        # Status bar
        self.status_var = tk.StringVar(value="✅ Ready to download")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=10, pady=(0, 5))
        
    def check_all_dependencies(self):
        """Check all required dependencies"""
        # First check yt-dlp
        yt_dlp_installed = self.check_yt_dlp()
        
        if yt_dlp_installed:
            # Then check JavaScript runtime
            self.check_js_dependencies()
    
    def check_yt_dlp(self):
        """Check if yt-dlp is installed"""
        try:
            result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.status_var.set(f"✅ yt-dlp v{result.stdout.strip()} found")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        response = messagebox.askyesno(
            "Dependency Missing",
            "yt-dlp is required but not installed. Would you like to install it now?"
        )
        if response:
            self.install_yt_dlp()
        else:
            messagebox.showerror("Error", "yt-dlp is required to run this application")
            self.root.quit()
            return False
        return True
    
    def check_js_dependencies(self):
        """Check for JavaScript runtime and ejs package"""
        js_runtime_found = False
        runtime_name = ""
        
        # Check for Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                js_runtime_found = True
                runtime_name = f"Node.js {result.stdout.strip()}"
                self.status_var.set(f"✅ {runtime_name} found")
        except FileNotFoundError:
            pass
        
        # If no Node.js, check for Deno as a fallback
        if not js_runtime_found:
            try:
                result = subprocess.run(["deno", "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    js_runtime_found = True
                    runtime_name = "Deno"
                    self.status_var.set("✅ Deno found")
            except FileNotFoundError:
                pass
        
        # Check for yt-dlp-ejs package
        ejs_installed = False
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "yt-dlp-ejs"],
                capture_output=True, text=True
            )
            ejs_installed = result.returncode == 0
            if ejs_installed:
                self.status_var.set("✅ yt-dlp-ejs package found")
        except Exception:
            pass
        
        # If JS runtime is missing, show warning
        if not js_runtime_found:
            response = messagebox.askyesno(
                "JavaScript Runtime Missing",
                "yt-dlp now requires Node.js (or Deno) for YouTube downloads.\n\n"
                "Would you like to open the Node.js download page?\n\n"
                "After installing Node.js, you'll also need to install the ejs package.\n"
                "The app will help you install it after Node.js is set up."
            )
            if response:
                webbrowser.open("https://nodejs.org/")
                messagebox.showinfo(
                    "Installation Steps",
                    "1. Download and install Node.js (LTS version)\n"
                    "2. Make sure 'Add to PATH' is checked during installation\n"
                    "3. Click OK and the app will help you install the remaining package"
                )
                # Check again after user installs
                self.root.after(5000, self.check_js_dependencies)
            return False
        
        # If JS runtime is found but ejs is missing, offer to install it
        elif not ejs_installed:
            response = messagebox.askyesno(
                "Missing Package",
                f"The required 'yt-dlp-ejs' package is not installed.\n\n"
                f"Would you like to install it now?"
            )
            if response:
                self.install_ejs_package()
            else:
                return False
        
        return True
    
    def install_yt_dlp(self):
        """Install yt-dlp using pip"""
        try:
            self.progress_var.set("Installing yt-dlp...")
            self.progress_bar.start()
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
                capture_output=True,
                text=True
            )
            
            self.progress_bar.stop()
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "yt-dlp installed successfully!")
                self.progress_var.set("Ready")
                self.status_var.set("✅ yt-dlp installed")
            else:
                messagebox.showerror("Error", f"Failed to install yt-dlp:\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
    
    def install_ejs_package(self):
        """Install yt-dlp-ejs package"""
        try:
            self.progress_var.set("Installing yt-dlp-ejs...")
            self.progress_bar.start()
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", "yt-dlp-ejs"],
                capture_output=True,
                text=True
            )
            
            self.progress_bar.stop()
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "yt-dlp-ejs installed successfully!")
                self.progress_var.set("Ready")
                self.status_var.set("✅ yt-dlp-ejs installed")
            else:
                messagebox.showerror("Error", f"Failed to install yt-dlp-ejs:\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
        finally:
            self.progress_bar.stop()
    
    def toggle_folder_entry(self):
        """Enable/disable folder entry based on checkbox"""
        if self.auto_folder_var.get():
            self.folder_entry.config(state='disabled')
        else:
            self.folder_entry.config(state='normal')
    
    def browse_folder(self):
        """Browse for folder"""
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.folder_path_var.set(folder)
    
    def update_quality_options(self):
        """Update quality options based on selected format"""
        if self.format_var.get() == "mp3":
            self.quality_combo.config(state='disabled')
            self.quality_var.set("audio only")
        else:
            self.quality_combo.config(state='readonly')
            if self.format_var.get() == "best":
                self.quality_combo.config(state='disabled')
                self.quality_var.set("best quality")
            else:
                self.quality_combo.config(state='readonly')
                self.quality_var.set("720p")
    
    def update_fetch_loading(self, text, is_loading=False):
        """Update loading indicator for fetch operation"""
        self.fetch_loading.config(text=text)
        if is_loading:
            self.fetch_btn.config(state='disabled')
            self.root.update()
        else:
            self.fetch_btn.config(state='normal')
    
    def fetch_content(self):
        """Fetch video/playlist information"""
        if self.fetch_in_progress:
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
        
        # Clear previous data
        self.clear_tree()
        self.playlist_videos = []
        self.selected_videos.clear()
        
        # Disable fetch button during operation
        self.fetch_in_progress = True
        self.update_fetch_loading("⏳ Fetching...", True)
        self.status_var.set("🔄 Fetching content...")
        
        # Start fetching in a separate thread
        Thread(target=self._fetch_content_thread, args=(url,), daemon=True).start()
    
    def _fetch_content_thread(self, url):
        """Thread function to fetch content"""
        try:
            self.root.after(0, lambda: self.progress_var.set("Fetching content..."))
            self.root.after(0, self.progress_bar.start)
            
            # First, check if it's a playlist or single video
            check_cmd = [
                "yt-dlp",
                "--dump-json",
                "--playlist-end", "1",
                "--extractor-args", "youtube:player_client=default",
                url
            ]
            
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                error_msg = check_result.stderr
                if "JavaScript runtime" in error_msg:
                    self.root.after(0, lambda: messagebox.showerror(
                        "JavaScript Runtime Error",
                        "JavaScript runtime is required but not properly configured.\n\n"
                        "Please run the dependency check again by restarting the app."
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch: {error_msg}"))
                return
            
            # Parse the output to determine if it's a playlist
            first_item = json.loads(check_result.stdout.strip().split('\n')[0])
            is_playlist = 'playlist_count' in first_item and first_item['playlist_count'] > 1
            
            videos = []
            playlist_title = first_item.get('playlist', first_item.get('title', 'Unknown'))
            
            if is_playlist:
                # It's a playlist - fetch all videos
                self.root.after(0, lambda: self.update_fetch_loading(f"⏳ Fetching playlist ({first_item['playlist_count']} videos)...", True))
                
                cmd = [
                    "yt-dlp",
                    "--flat-playlist",
                    "--dump-json",
                    "--extractor-args", "youtube:player_client=default",
                    url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            try:
                                video_info = json.loads(line)
                                videos.append({
                                    'title': video_info.get('title', 'Unknown'),
                                    'url': f"https://youtube.com/watch?v={video_info.get('id')}",
                                    'index': video_info.get('playlist_index', len(videos) + 1),
                                    'duration': 'Unknown',
                                    'formats': ['Multiple qualities'],
                                    'size': '~50 MB',
                                    'playlist_title': playlist_title
                                })
                            except json.JSONDecodeError:
                                continue
            else:
                # Single video
                self.root.after(0, lambda: self.update_fetch_loading("⏳ Fetching video info...", True))
                
                # Get detailed video info
                cmd = [
                    "yt-dlp",
                    "--dump-json",
                    "--extractor-args", "youtube:player_client=default",
                    url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout:
                    video_info = json.loads(result.stdout)
                    
                    # Get format info
                    duration = video_info.get('duration', 0)
                    duration_str = self.format_duration(duration)
                    
                    # Estimate size based on duration and quality
                    est_size = self.estimate_size(duration, '720p')
                    
                    videos = [{
                        'title': video_info.get('title', 'Unknown'),
                        'url': url,
                        'index': 1,
                        'duration': duration_str,
                        'formats': ['720p', '1080p', '480p'],
                        'size': est_size,
                        'playlist_title': video_info.get('title', 'Unknown')
                    }]
            
            self.root.after(0, self._update_tree, videos)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.fetch_in_progress = False
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.progress_var.set("Ready"))
            self.root.after(0, lambda: self.update_fetch_loading("", False))
            self.root.after(0, lambda: self.status_var.set(f"✅ Found {len(videos)} video(s)"))
    
    def estimate_size(self, duration_seconds, quality):
        """Estimate file size based on duration and quality"""
        if not duration_seconds:
            return "~50 MB"
        
        # Rough estimates: 1 min = ~10MB for 720p, ~20MB for 1080p, etc.
        minutes = duration_seconds / 60
        
        if quality == '2160p (4K)':
            size_mb = minutes * 50
        elif quality == '1080p':
            size_mb = minutes * 20
        elif quality == '720p':
            size_mb = minutes * 10
        elif quality == '480p':
            size_mb = minutes * 6
        else:
            size_mb = minutes * 10
        
        if size_mb < 1:
            return "< 1 MB"
        elif size_mb < 1000:
            return f"~{int(size_mb)} MB"
        else:
            return f"~{size_mb/1000:.1f} GB"
    
    def format_duration(self, seconds):
        """Format duration in seconds to MM:SS or HH:MM:SS"""
        if not seconds:
            return "00:00"
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        except:
            return "00:00"
    
    def _update_tree(self, videos):
        """Update the tree with fetched videos"""
        self.playlist_videos = videos
        
        for i, video in enumerate(videos, 1):
            # Truncate title if too long
            title = video['title']
            if len(title) > 60:
                title = title[:57] + "..."
            
            self.tree.insert("", tk.END, values=(
                "☐",  # Unchecked checkbox
                i,
                title,
                video['duration'],
                ", ".join(video['formats'][:3]),
                video['size']
            ), iid=f"video_{i}")
    
    def on_tree_click(self, event):
        """Handle clicks on the tree to toggle checkboxes"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":  # First column (checkbox)
                item = self.tree.identify_row(event.y)
                if item:
                    self.toggle_checkbox(item)
    
    def toggle_checkbox(self, item):
        """Toggle checkbox state"""
        current_values = self.tree.item(item, "values")
        checkbox = current_values[0]
        index = int(current_values[1])
        
        if checkbox == "☐":
            new_checkbox = "☑"
            self.selected_videos.add(index)
        else:
            new_checkbox = "☐"
            self.selected_videos.discard(index)
        
        self.tree.item(item, values=(new_checkbox, *current_values[1:]))
        self.status_var.set(f"📌 {len(self.selected_videos)} video(s) selected")
    
    def select_all(self):
        """Select all videos"""
        for i, item in enumerate(self.tree.get_children(), 1):
            self.tree.item(item, values=("☑", i, 
                self.tree.item(item, "values")[2],
                self.tree.item(item, "values")[3],
                self.tree.item(item, "values")[4],
                self.tree.item(item, "values")[5]))
            self.selected_videos.add(i)
        self.status_var.set(f"📌 {len(self.selected_videos)} video(s) selected")
    
    def deselect_all(self):
        """Deselect all videos"""
        for i, item in enumerate(self.tree.get_children(), 1):
            self.tree.item(item, values=("☐", i,
                self.tree.item(item, "values")[2],
                self.tree.item(item, "values")[3],
                self.tree.item(item, "values")[4],
                self.tree.item(item, "values")[5]))
            self.selected_videos.discard(i)
        self.status_var.set("📌 0 video(s) selected")
    
    def clear_all(self):
        """Clear all data and reset UI"""
        self.clear_tree()
        self.playlist_videos = []
        self.selected_videos.clear()
        self.url_var.set("")
        self.status_var.set("✅ Ready to download")
        self.progress_var.set("Ready")
        self.current_download_var.set("")
    
    def get_download_folder(self):
        """Determine download folder based on user choices"""
        if self.auto_folder_var.get() and self.playlist_videos:
            # Create folder from playlist/video title
            folder_name = self.playlist_videos[0]['playlist_title']
            # Clean folder name
            folder_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            
            # Use current directory or custom parent folder
            if self.folder_path_var.get():
                base_folder = self.folder_path_var.get()
            else:
                base_folder = os.path.expanduser("~/Downloads")
            
            folder_path = os.path.join(base_folder, folder_name)
            
            # Create folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                self.status_var.set(f"📁 Created folder: {folder_name}")
            
            return folder_path
        elif self.folder_path_var.get():
            # Use custom folder
            return self.folder_path_var.get()
        else:
            # Ask user for folder
            return filedialog.askdirectory(title="Select Download Directory")
    
    def start_download(self):
        """Start downloading selected videos"""
        if not self.selected_videos:
            messagebox.showwarning("Warning", "No videos selected")
            return
        
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress")
            return
        
        # Get download folder
        download_dir = self.get_download_folder()
        if not download_dir:
            return
        
        # Confirm download
        response = messagebox.askyesno(
            "Confirm Download",
            f"Download {len(self.selected_videos)} video(s) to:\n{download_dir}\n\n"
            f"Format: {self.format_var.get().upper()}\n"
            f"Quality: {self.quality_var.get()}\n\n"
            f"Continue?"
        )
        
        if not response:
            return
        
        # Disable download button
        self.download_btn.config(state='disabled')
        
        # Start download in separate thread
        self.is_downloading = True
        Thread(target=self._download_thread, args=(download_dir,), daemon=True).start()
    
    def _download_thread(self, download_dir):
        """Thread function to download videos - FIXED for merged output"""
        try:
            self.root.after(0, self.progress_bar.start)
            
            total = len(self.selected_videos)
            completed = 0
            failed = []
            
            for index in sorted(self.selected_videos):
                video = self.playlist_videos[index - 1]
                
                self.root.after(0, lambda: self.current_download_var.set(f"📥 Downloading: {video['title']}"))
                self.root.after(0, lambda: self.progress_var.set(f"Progress: {completed}/{total}"))
                self.root.after(0, lambda: self.status_var.set(f"📥 Downloading {completed+1}/{total}: {video['title'][:30]}..."))
                
                # Build download command based on format and quality
                format_type = self.format_var.get()
                quality = self.quality_var.get()
                
                # Base command with common options
                cmd = [
                    "yt-dlp",
                    "--extractor-args", "youtube:player_client=default",
                    "--no-playlist",  # Don't download playlist, just single video
                    "--progress",
                    "--newline",
                    "-o", os.path.join(download_dir, "%(title)s.%(ext)s")
                ]
                
                # CRITICAL FIX: Use format selection that downloads pre-merged formats when possible
                if format_type == "mp3":
                    # For MP3 audio - extract audio only
                    cmd.extend([
                        "-f", "bestaudio/best",
                        "-x",  # Extract audio
                        "--audio-format", "mp3",
                        "--audio-quality", "0",  # Best quality
                        "--embed-thumbnail",  # Add thumbnail as cover art
                        "--add-metadata"
                    ])
                elif format_type == "mp4":
                    # For MP4 - try to get formats with both video and audio already merged
                    # First try to get format that has both video and audio
                    if quality == "2160p (4K)":
                        cmd.extend(["-f", "best[height<=2160][ext=mp4]/best[height<=2160]"])
                    elif quality == "1440p (2K)":
                        cmd.extend(["-f", "best[height<=1440][ext=mp4]/best[height<=1440]"])
                    elif quality == "1080p":
                        cmd.extend(["-f", "best[height<=1080][ext=mp4]/best[height<=1080]"])
                    elif quality == "720p":
                        cmd.extend(["-f", "best[height<=720][ext=mp4]/best[height<=720]"])
                    elif quality == "480p":
                        cmd.extend(["-f", "best[height<=480][ext=mp4]/best[height<=480]"])
                    elif quality == "360p":
                        cmd.extend(["-f", "best[height<=360][ext=mp4]/best[height<=360]"])
                    elif quality == "240p":
                        cmd.extend(["-f", "best[height<=240][ext=mp4]/best[height<=240]"])
                    else:
                        cmd.extend(["-f", "best[ext=mp4]/best"])
                        
                elif format_type == "webm":
                    # For WebM - try to get formats with both video and audio already merged
                    if quality == "2160p (4K)":
                        cmd.extend(["-f", "best[height<=2160][ext=webm]/best[height<=2160]"])
                    elif quality == "1440p (2K)":
                        cmd.extend(["-f", "best[height<=1440][ext=webm]/best[height<=1440]"])
                    elif quality == "1080p":
                        cmd.extend(["-f", "best[height<=1080][ext=webm]/best[height<=1080]"])
                    elif quality == "720p":
                        cmd.extend(["-f", "best[height<=720][ext=webm]/best[height<=720]"])
                    elif quality == "480p":
                        cmd.extend(["-f", "best[height<=480][ext=webm]/best[height<=480]"])
                    elif quality == "360p":
                        cmd.extend(["-f", "best[height<=360][ext=webm]/best[height<=360]"])
                    elif quality == "240p":
                        cmd.extend(["-f", "best[height<=240][ext=webm]/best[height<=240]"])
                    else:
                        cmd.extend(["-f", "best[ext=webm]/best"])
                        
                elif format_type == "best":
                    # For best quality - let yt-dlp choose but prefer merged formats
                    cmd.extend(["-f", "best/bestvideo+bestaudio"])
                
                # Add subtitles if requested
                if self.subtitles_var.get():
                    cmd.extend([
                        "--write-subs",
                        "--sub-lang", "en",
                        "--embed-subs"
                    ])
                
                # Add thumbnail if requested
                if self.thumbnail_var.get():
                    cmd.extend([
                        "--write-thumbnail",
                        "--embed-thumbnail"
                    ])
                
                # Add URL
                cmd.append(video['url'])
                
                # Print command for debugging (optional)
                print(f"Running command: {' '.join(cmd)}")
                
                # Execute download with real-time output
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Read output in real-time
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            # Update UI with progress
                            if '%' in output:
                                # Extract percentage
                                match = re.search(r'(\d+\.?\d*)%', output)
                                if match:
                                    percent = match.group(1)
                                    self.root.after(0, lambda p=percent: self.current_download_var.set(f"Downloading... {p}%"))
                                else:
                                    self.root.after(0, lambda o=output.strip(): self.current_download_var.set(o))
                    
                    # Get the return code
                    return_code = process.poll()
                    
                    # Read any error output
                    stderr = process.stderr.read()
                    
                    if return_code == 0:
                        completed += 1
                        self.root.after(0, lambda: self.status_var.set(f"✅ Completed: {video['title'][:30]}..."))
                    else:
                        error_msg = stderr if stderr else "Unknown error"
                        failed.append(f"{video['title']}")
                        print(f"Download failed: {error_msg}")
                        
                except Exception as e:
                    failed.append(f"{video['title']}")
                    print(f"Exception during download: {str(e)}")
            
            # Show completion message
            self.root.after(0, self.progress_bar.stop)
            
            if failed:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Partial Success", 
                    f"✅ {completed} downloads completed\n"
                    f"❌ {len(failed)} failed:\n" + "\n".join(failed[:5])
                ))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"✅ All {completed} downloads completed successfully!\n"
                    f"📁 Saved to: {download_dir}"
                ))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.is_downloading = False
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.progress_var.set("Ready"))
            self.root.after(0, lambda: self.current_download_var.set(""))
            self.root.after(0, lambda: self.status_var.set("✅ Download completed"))
            self.root.after(0, lambda: self.download_btn.config(state='normal'))
    
    def clear_tree(self):
        """Clear all items from the tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)

def main():
    root = tk.Tk()
    
    # Set style
    style = ttk.Style()
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
    
    # Create app
    app = YouTubeDownloader(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()