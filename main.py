import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import os
import re
import json
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen
from threading import Thread
import queue

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("800x600")
        
        # Data structures
        self.playlist_videos = []
        self.selected_videos = set()
        self.download_queue = queue.Queue()
        self.is_downloading = False
        
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
        
        # Content Display Frame
        content_frame = ttk.LabelFrame(self.root, text="Content", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for displaying videos
        self.tree = ttk.Treeview(content_frame, columns=("selected", "index", "title", "url"), show="headings")
        self.tree.heading("selected", text="✓")
        self.tree.heading("index", text="#")
        self.tree.heading("title", text="Title")
        self.tree.heading("url", text="URL")
        
        self.tree.column("selected", width=40, anchor=tk.CENTER)
        self.tree.column("index", width=50, anchor=tk.CENTER)
        self.tree.column("title", width=400)
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
        ttk.Button(control_frame, text="Download Selected", command=self.start_download).pack(side=tk.LEFT, padx=5)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(self.root, text="Download Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
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
        
        # Start fetching in a separate thread
        Thread(target=self._fetch_content_thread, args=(url,), daemon=True).start()
    
    def _fetch_content_thread(self, url):
        """Thread function to fetch content"""
        try:
            self.progress_var.set("Fetching content...")
            self.progress_bar.start()
            
            # Use yt-dlp to get video information
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                url
            ]
            
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
                        videos.append({
                            'title': video_info.get('title', 'Unknown'),
                            'url': video_info.get('webpage_url', '') or video_info.get('url', ''),
                            'index': video_info.get('playlist_index', len(videos) + 1)
                        })
                    except json.JSONDecodeError:
                        continue
            
            if not videos:
                # Single video case
                cmd = ["yt-dlp", "--dump-json", url]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout:
                    video_info = json.loads(result.stdout)
                    videos = [{
                        'title': video_info.get('title', 'Unknown'),
                        'url': video_info.get('webpage_url', url),
                        'index': 1
                    }]
            
            self.root.after(0, self._update_tree, videos)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, self.progress_bar.stop)
            self.root.after(0, lambda: self.progress_var.set("Ready"))
    
    def _update_tree(self, videos):
        """Update the tree with fetched videos"""
        self.playlist_videos = videos
        
        for i, video in enumerate(videos, 1):
            self.tree.insert("", tk.END, values=(
                "☐",  # Unchecked checkbox
                i,
                video['title'],
                video['url']
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
    
    def select_all(self):
        """Select all videos"""
        for i, item in enumerate(self.tree.get_children(), 1):
            self.tree.item(item, values=("☑", i, self.playlist_videos[i-1]['title'], self.playlist_videos[i-1]['url']))
            self.selected_videos.add(i)
    
    def deselect_all(self):
        """Deselect all videos"""
        for i, item in enumerate(self.tree.get_children(), 1):
            self.tree.item(item, values=("☐", i, self.playlist_videos[i-1]['title'], self.playlist_videos[i-1]['url']))
            self.selected_videos.discard(i)
    
    def start_download(self):
        """Start downloading selected videos"""
        if not self.selected_videos:
            messagebox.showwarning("Warning", "No videos selected")
            return
        
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress")
            return
        
        # Ask for download directory
        download_dir = filedialog.askdirectory(title="Select Download Directory")
        if not download_dir:
            return
        
        # Start download in separate thread
        self.is_downloading = True
        Thread(target=self._download_thread, args=(download_dir,), daemon=True).start()
    
    def _download_thread(self, download_dir):
        """Thread function to download videos"""
        try:
            self.root.after(0, self.progress_bar.start)
            
            for index in sorted(self.selected_videos):
                video = self.playlist_videos[index - 1]
                
                self.root.after(0, lambda: self.progress_var.set(f"Downloading: {video['title']}"))
                
                # Download video using yt-dlp
                cmd = [
                    "yt-dlp",
                    "-o", os.path.join(download_dir, "%(title)s.%(ext)s"),
                    video['url']
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to download {video['title']}: {result.stderr}"))
                    continue
            
            self.root.after(0, lambda: messagebox.showinfo("Success", "All downloads completed!"))
            
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