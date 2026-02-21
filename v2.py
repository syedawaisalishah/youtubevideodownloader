import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import os
import json
from threading import Thread
from datetime import datetime

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("900x700")
        
        # Data structures
        self.playlist_videos = []
        self.selected_videos = set()
        self.is_downloading = False
        self.download_folder = ""
        self.playlist_title = ""
        
        self.setup_ui()
        self.check_dependencies()
        
    def setup_ui(self):
        """Setup the main UI elements"""
        # URL Input Frame
        url_frame = ttk.LabelFrame(self.root, text="Enter URL", padding=10)
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=70)
        url_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(url_frame, text="Fetch", command=self.fetch_content).pack(side=tk.LEFT)
        
        # Folder Selection Frame
        folder_frame = ttk.LabelFrame(self.root, text="Download Location", padding=10)
        folder_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.folder_var = tk.StringVar(value="No folder selected")
        folder_label = ttk.Label(folder_frame, textvariable=self.folder_var, width=60)
        folder_label.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT)
        ttk.Button(folder_frame, text="Create New Folder", command=self.create_new_folder).pack(side=tk.LEFT, padx=5)
        
        # Playlist Info Frame
        self.info_frame = ttk.LabelFrame(self.root, text="Playlist Information", padding=10)
        self.info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.playlist_title_var = tk.StringVar(value="No playlist loaded")
        ttk.Label(self.info_frame, textvariable=self.playlist_title_var, font=('Arial', 10, 'bold')).pack()
        
        # Content Display Frame
        content_frame = ttk.LabelFrame(self.root, text="Content", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for displaying videos
        self.tree = ttk.Treeview(content_frame, columns=("selected", "index", "title", "duration", "url"), show="headings")
        self.tree.heading("selected", text="✓")
        self.tree.heading("index", text="#")
        self.tree.heading("title", text="Title")
        self.tree.heading("duration", text="Duration")
        self.tree.heading("url", text="URL")
        
        self.tree.column("selected", width=40, anchor=tk.CENTER)
        self.tree.column("index", width=50, anchor=tk.CENTER)
        self.tree.column("title", width=400)
        self.tree.column("duration", width=100, anchor=tk.CENTER)
        self.tree.column("url", width=200)
        
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
        
        ttk.Button(control_frame, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Create Playlist Folder", command=self.create_playlist_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Download Selected", command=self.start_download).pack(side=tk.LEFT, padx=5)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(self.root, text="Download Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready to download")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def check_dependencies(self):
        """Check if yt-dlp is installed"""
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            response = messagebox.askyesno(
                "Dependency Missing",
                "yt-dlp is required but not installed. Would you like to install it now?"
            )
            if response:
                self.install_yt_dlp()
            else:
                messagebox.showerror("Error", "yt-dlp is required to run this application")
                self.root.quit()
    
    def install_yt_dlp(self):
        """Install yt-dlp using pip"""
        try:
            self.progress_var.set("Installing yt-dlp...")
            self.progress_bar.start()
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "yt-dlp"],
                capture_output=True,
                text=True
            )
            
            self.progress_bar.stop()
            
            if result.returncode == 0:
                messagebox.showinfo("Success", "yt-dlp installed successfully!")
                self.progress_var.set("Ready")
            else:
                messagebox.showerror("Error", f"Failed to install yt-dlp:\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Installation failed: {str(e)}")
    
    def browse_folder(self):
        """Browse for download folder"""
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.download_folder = folder
            self.folder_var.set(folder)
            self.status_var.set(f"Download folder set to: {folder}")
    
    def create_new_folder(self):
        """Create a new folder"""
        parent_folder = filedialog.askdirectory(title="Select Parent Folder")
        if parent_folder:
            folder_name = tk.simpledialog.askstring("Folder Name", "Enter new folder name:")
            if folder_name:
                try:
                    new_folder = os.path.join(parent_folder, folder_name)
                    os.makedirs(new_folder, exist_ok=True)
                    self.download_folder = new_folder
                    self.folder_var.set(new_folder)
                    self.status_var.set(f"Created and selected folder: {new_folder}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create folder: {str(e)}")
    
    def create_playlist_folder(self):
        """Create a folder named after the playlist"""
        if not self.playlist_title:
            messagebox.showwarning("Warning", "No playlist loaded. Please fetch a playlist first.")
            return
        
        if not self.download_folder:
            messagebox.showwarning("Warning", "Please select a parent folder first.")
            return
        
        # Create folder name from playlist title (sanitize for filesystem)
        folder_name = self.sanitize_filename(self.playlist_title)
        playlist_folder = os.path.join(self.download_folder, folder_name)
        
        try:
            os.makedirs(playlist_folder, exist_ok=True)
            self.download_folder = playlist_folder
            self.folder_var.set(playlist_folder)
            self.status_var.set(f"Created playlist folder: {folder_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create playlist folder: {str(e)}")
    
    def sanitize_filename(self, filename):
        """Remove invalid characters from filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()
    
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
        self.playlist_title = ""
        self.playlist_title_var.set("Fetching playlist information...")
        
        # Start fetching in a separate thread
        Thread(target=self._fetch_content_thread, args=(url,), daemon=True).start()
    
    def _fetch_content_thread(self, url):
        """Thread function to fetch content"""
        try:
            self.root.after(0, lambda: self.progress_var.set("Fetching content..."))
            self.root.after(0, self.progress_bar.start)
            
            # First, get playlist title
            cmd = ["yt-dlp", "--flat-playlist", "--dump-json", "--playlist-end", "1", url]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                first_item = json.loads(result.stdout.strip().split('\n')[0])
                self.playlist_title = first_item.get('playlist_title', 'Playlist')
                self.root.after(0, lambda: self.playlist_title_var.set(f"Playlist: {self.playlist_title}"))
            
            # Get all videos
            cmd = ["yt-dlp", "--flat-playlist", "--dump-json", url]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch: {result.stderr}"))
                return
            
            # Parse the output
            videos = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        video_info = json.loads(line)
                        
                        # Get duration for each video (optional, might be slow for large playlists)
                        duration = video_info.get('duration', 0)
                        duration_str = self.format_duration(duration) if duration else "Unknown"
                        
                        videos.append({
                            'title': video_info.get('title', 'Unknown'),
                            'url': video_info.get('webpage_url', '') or video_info.get('url', ''),
                            'index': video_info.get('playlist_index', len(videos) + 1),
                            'duration': duration_str
                        })
                    except json.JSONDecodeError:
                        continue
            
            if not videos:
                # Single video case
                cmd = ["yt-dlp", "--dump-json", url]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout:
                    video_info = json.loads(result.stdout)
                    duration = video_info.get('duration', 0)
                    videos = [{
                        'title': video_info.get('title', 'Unknown'),
                        'url': video_info.get('webpage_url', url),
                        'index': 1,
                        'duration': self.format_duration(duration) if duration else "Unknown"
                    }]
                    self.playlist_title = "Single Video"
                    self.root.after(0, lambda: self.playlist_title_var.set("Single Video"))
            
            self.root.after(0, self._update_tree, videos)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.progress_var.set("Ready"))
    
    def format_duration(self, seconds):
        """Format duration in seconds to HH:MM:SS"""
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
        
        for video in videos:
            self.tree.insert("", tk.END, values=(
                "☐",  # Unchecked checkbox
                video['index'],
                video['title'],
                video['duration'],
                video['url']
            ), iid=f"video_{video['index']}")
        
        self.status_var.set(f"Loaded {len(videos)} videos")
    
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
        self.status_var.set(f"Selected {len(self.selected_videos)} videos")
    
    def select_all(self):
        """Select all videos"""
        for i, item in enumerate(self.tree.get_children(), 1):
            video_data = self.playlist_videos[i-1]
            self.tree.item(item, values=(
                "☑", 
                video_data['index'], 
                video_data['title'], 
                video_data['duration'],
                video_data['url']
            ))
            self.selected_videos.add(i)
        self.status_var.set(f"Selected {len(self.selected_videos)} videos")
    
    def deselect_all(self):
        """Deselect all videos"""
        for i, item in enumerate(self.tree.get_children(), 1):
            video_data = self.playlist_videos[i-1]
            self.tree.item(item, values=(
                "☐", 
                video_data['index'], 
                video_data['title'], 
                video_data['duration'],
                video_data['url']
            ))
            self.selected_videos.discard(i)
        self.status_var.set("All videos deselected")
    
    def start_download(self):
        """Start downloading selected videos"""
        if not self.selected_videos:
            messagebox.showwarning("Warning", "No videos selected")
            return
        
        if not self.download_folder:
            response = messagebox.askyesno(
                "No Folder Selected",
                "No download folder selected. Would you like to select one now?"
            )
            if response:
                self.browse_folder()
                if not self.download_folder:  # User cancelled
                    return
            else:
                return
        
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress")
            return
        
        # Create playlist subfolder option
        if len(self.selected_videos) > 1 and self.playlist_title:
            response = messagebox.askyesno(
                "Create Playlist Folder",
                f"Would you like to create a folder named '{self.playlist_title}' for these downloads?"
            )
            if response:
                self.create_playlist_folder()
        
        # Start download in separate thread
        self.is_downloading = True
        Thread(target=self._download_thread, daemon=True).start()
    
    def _download_thread(self):
        """Thread function to download videos"""
        try:
            self.root.after(0, self.progress_bar.start)
            
            total = len(self.selected_videos)
            completed = 0
            
            for index in sorted(self.selected_videos):
                video = self.playlist_videos[index - 1]
                
                # Update status
                self.root.after(0, lambda: self.progress_var.set(f"Downloading ({completed+1}/{total}): {video['title'][:50]}..."))
                self.root.after(0, lambda: self.status_var.set(f"Downloading video {completed+1} of {total}"))
                
                # Download video using yt-dlp
                cmd = [
                    "yt-dlp",
                    "-o", os.path.join(self.download_folder, "%(title)s.%(ext)s"),
                    "--no-playlist",  # Download only single video
                    video['url']
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.root.after(0, lambda err=result.stderr, title=video['title']: 
                                   messagebox.showerror("Error", f"Failed to download {title}: {err}"))
                else:
                    completed += 1
                
                # Update progress
                self.root.after(0, lambda: self.progress_var.set(f"Completed {completed}/{total} videos"))
            
            # Download complete
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"Successfully downloaded {completed} out of {total} videos to:\n{self.download_folder}"
            ))
            self.root.after(0, lambda: self.status_var.set(f"Download complete! Files saved to: {self.download_folder}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.is_downloading = False
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.progress_var.set("Ready"))
    
    def clear_tree(self):
        """Clear all items from the tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)

def main():
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()