import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import os
import json
from threading import Thread
import queue
import webbrowser

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
        
        ttk.Button(right_buttons, text="📥 Download Selected", command=self.start_download, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
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
    
    def fetch_content(self):
        """Fetch video/playlist information"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
        
        # Clear previous data
        self.clear_tree()
        self.playlist_videos = []
        self.selected_videos.clear()
        
        # Disable fetch button during operation
        self.fetch_btn.config(state='disabled')
        self.status_var.set("🔄 Fetching content...")
        
        # Start fetching in a separate thread
        Thread(target=self._fetch_content_thread, args=(url,), daemon=True).start()
    
    def _fetch_content_thread(self, url):
        """Thread function to fetch content"""
        try:
            self.root.after(0, lambda: self.progress_var.set("Fetching content..."))
            self.root.after(0, self.progress_bar.start)
            
            # Get playlist info
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                "--extractor-args", "youtube:player_client=default",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                error_msg = result.stderr
                if "JavaScript runtime" in error_msg:
                    self.root.after(0, lambda: messagebox.showerror(
                        "JavaScript Runtime Error",
                        "JavaScript runtime is required but not properly configured.\n\n"
                        "Please run the dependency check again by restarting the app."
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch: {error_msg}"))
                return
            
            # Parse the output
            videos = []
            playlist_title = "Unknown Playlist"
            
            # Try to get playlist title
            info_cmd = ["yt-dlp", "--dump-json", "--playlist-end", "1", "--extractor-args", "youtube:player_client=default", url]
            info_result = subprocess.run(info_cmd, capture_output=True, text=True)
            if info_result.returncode == 0 and info_result.stdout:
                try:
                    info = json.loads(info_result.stdout.strip().split('\n')[0])
                    playlist_title = info.get('playlist_title', info.get('title', 'Unknown Playlist'))
                except:
                    pass
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        video_info = json.loads(line)
                        
                        # Get individual video info for duration and formats
                        video_url = video_info.get('webpage_url', '') or video_info.get('url', '')
                        if video_url:
                            format_cmd = ["yt-dlp", "-F", "--extractor-args", "youtube:player_client=default", video_url]
                            format_result = subprocess.run(format_cmd, capture_output=True, text=True)
                            available_formats, estimated_size = self.parse_formats(format_result.stdout)
                        else:
                            available_formats = ["Various qualities available"]
                            estimated_size = "~50 MB"
                        
                        videos.append({
                            'title': video_info.get('title', 'Unknown'),
                            'url': video_url,
                            'index': video_info.get('playlist_index', len(videos) + 1),
                            'duration': self.format_duration(video_info.get('duration', 0)),
                            'formats': available_formats,
                            'size': estimated_size,
                            'playlist_title': playlist_title
                        })
                    except json.JSONDecodeError:
                        continue
            
            if not videos:
                # Single video case
                cmd = ["yt-dlp", "--dump-json", "--extractor-args", "youtube:player_client=default", url]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout:
                    video_info = json.loads(result.stdout)
                    
                    # Get available formats
                    format_cmd = ["yt-dlp", "-F", "--extractor-args", "youtube:player_client=default", url]
                    format_result = subprocess.run(format_cmd, capture_output=True, text=True)
                    available_formats, estimated_size = self.parse_formats(format_result.stdout)
                    
                    videos = [{
                        'title': video_info.get('title', 'Unknown'),
                        'url': video_info.get('webpage_url', url),
                        'index': 1,
                        'duration': self.format_duration(video_info.get('duration', 0)),
                        'formats': available_formats,
                        'size': estimated_size,
                        'playlist_title': video_info.get('title', 'Unknown')
                    }]
            
            self.root.after(0, self._update_tree, videos)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.progress_var.set("Ready"))
            self.root.after(0, lambda: self.fetch_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_var.set("✅ Content fetched successfully"))
    
    def parse_formats(self, format_output):
        """Parse available formats from yt-dlp -F output"""
        formats = []
        sizes = []
        lines = format_output.split('\n')
        
        for line in lines:
            # Look for lines with resolution info
            if 'x' in line and ('mp4' in line or 'webm' in line):
                parts = line.split()
                for part in parts:
                    if 'x' in part and any(q in part for q in ['144', '240', '360', '480', '720', '1080', '1440', '2160']):
                        formats.append(part)
                        # Try to extract file size
                        for i, p in enumerate(parts):
                            if 'MiB' in p or 'KiB' in p:
                                sizes.append(p)
                                break
                        break
        
        # Estimate average size if available
        estimated_size = "~50 MB"
        if sizes:
            # Simple size estimation
            avg_size = "~25 MB" if '240' in str(formats) else "~50 MB" if '720' in str(formats) else "~150 MB"
            estimated_size = avg_size
        
        return formats[:5] if formats else ["Multiple qualities"], estimated_size
    
    def format_duration(self, seconds):
        """Format duration in seconds to MM:SS or HH:MM:SS"""
        if not seconds:
            return "00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _update_tree(self, videos):
        """Update the tree with fetched videos"""
        self.playlist_videos = videos
        
        for i, video in enumerate(videos, 1):
            formats_display = ", ".join(video['formats'][:3])  # Show first 3 formats
            if len(video['formats']) > 3:
                formats_display += f" +{len(video['formats'])-3} more"
            
            # Truncate title if too long
            title = video['title']
            if len(title) > 60:
                title = title[:57] + "..."
            
            self.tree.insert("", tk.END, values=(
                "☐",  # Unchecked checkbox
                i,
                title,
                video['duration'],
                formats_display,
                video['size']
            ), iid=f"video_{i}")
        
        self.status_var.set(f"✅ Found {len(videos)} video(s)")
    
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
        
        # Start download in separate thread
        self.is_downloading = True
        Thread(target=self._download_thread, args=(download_dir,), daemon=True).start()
    
    def _download_thread(self, download_dir):
        """Thread function to download videos"""
        try:
            self.root.after(0, self.progress_bar.start)
            
            total = len(self.selected_videos)
            completed = 0
            failed = []
            
            for index in sorted(self.selected_videos):
                video = self.playlist_videos[index - 1]
                
                self.root.after(0, lambda: self.current_download_var.set(f"📥 Downloading: {video['title']}"))
                self.root.after(0, lambda: self.progress_var.set(f"Progress: {completed}/{total}"))
                self.root.after(0, lambda: self.status_var.set(f"📥 Downloading {completed+1}/{total}..."))
                
                # Build download command based on format and quality
                cmd = [
                    "yt-dlp",
                    "--extractor-args", "youtube:player_client=default",
                    "--progress",
                    "--newline"
                ]
                
                # Format and quality options
                format_type = self.format_var.get()
                quality = self.quality_var.get()
                
                if format_type == "mp3":
                    # Extract audio as MP3
                    cmd.extend([
                        "-x",
                        "--audio-format", "mp3",
                        "--audio-quality", "0",  # Best quality
                        "-o", os.path.join(download_dir, "%(title)s.%(ext)s")
                    ])
                elif format_type == "best":
                    # Best quality video+audio
                    cmd.extend([
                        "-f", "bestvideo+bestaudio/best",
                        "--merge-output-format", "mp4",
                        "-o", os.path.join(download_dir, "%(title)s.%(ext)s")
                    ])
                else:
                    # Specific quality for video
                    quality_map = {
                        "2160p (4K)": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
                        "1440p (2K)": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
                        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
                        "240p": "bestvideo[height<=240]+bestaudio/best[height<=240]"
                    }
                    
                    format_spec = quality_map.get(quality, "best[height<=720]")
                    
                    cmd.extend([
                        "-f", format_spec,
                        "--merge-output-format", format_type,
                        "-o", os.path.join(download_dir, "%(title)s.%(ext)s")
                    ])
                
                # Add subtitles if requested
                if self.subtitles_var.get():
                    cmd.extend(["--write-subs", "--sub-lang", "en"])
                
                # Add thumbnail if requested
                if self.thumbnail_var.get():
                    cmd.append("--write-thumbnail")
                
                # Add URL
                cmd.append(video['url'])
                
                # Execute download
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    failed.append(video['title'])
                else:
                    completed += 1
            
            # Show completion message
            if failed:
                messagebox.showwarning(
                    "Partial Success", 
                    f"✅ {completed} downloads completed\n"
                    f"❌ {len(failed)} failed:\n" + "\n".join(failed[:5])
                )
            else:
                messagebox.showinfo(
                    "Success", 
                    f"✅ All {completed} downloads completed successfully!\n"
                    f"📁 Saved to: {download_dir}"
                )
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.is_downloading = False
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.progress_var.set("Ready"))
            self.root.after(0, lambda: self.current_download_var.set(""))
            self.root.after(0, lambda: self.status_var.set("✅ Download completed"))
    
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