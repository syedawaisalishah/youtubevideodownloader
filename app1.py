import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import json
import threading
import os
import sys
import requests
from PIL import Image, ImageTk
from io import BytesIO

# -----------------------------
# Base path for ffmpeg (works in .py and .exe)
# -----------------------------
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

ffmpeg_path = os.path.join(base_path, "ffmpeg")  # folder containing ffmpeg.exe

# -----------------------------
# Globals
# -----------------------------
process = None
format_options = {}
download_path = os.path.join(os.path.expanduser("~"), "Downloads")

# -----------------------------
# Check yt-dlp
# -----------------------------
def has_ytdlp():
    try:
        subprocess.run(["yt-dlp", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except:
        return False

# -----------------------------
# Fetch formats + preview
# -----------------------------
def fetch_formats():
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Please enter a video URL.")
        return

    status_label.config(text="Fetching video info...")
    root.update_idletasks()

    try:
        result = subprocess.run(["yt-dlp", url, "--dump-json"], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        # Show title
        title_label.config(text=data.get("title", "Unknown Title"))

        # Show thumbnail
        thumbnail_url = data.get("thumbnail")
        if thumbnail_url:
            response = requests.get(thumbnail_url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img = img.resize((320, 180))
            img = ImageTk.PhotoImage(img)
            thumbnail_label.config(image=img)
            thumbnail_label.image = img

        # Load MP4 video formats (video only)
        formats = data.get("formats", [])
        format_options.clear()
        available_formats = []

        for f in formats:
            if f.get("vcodec") != "none" and f.get("ext") == "mp4":
                height = f.get("height")
                if height:
                    label = f"{height}p"
                    format_options[label] = f["format_id"]
                    available_formats.append(label)

        # Sort available formats ascending by resolution
        available_formats = sorted(list(set(available_formats)), key=lambda x: int(x.replace("p","")))
        format_dropdown["values"] = available_formats

        if available_formats:
            format_dropdown.current(len(available_formats)-1)  # default highest quality
            status_label.config(text="Formats loaded.")
        else:
            status_label.config(text="No MP4 formats found.")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text="Error fetching info.")

# -----------------------------
# Choose download folder
# -----------------------------
def choose_folder():
    global download_path
    path = filedialog.askdirectory()
    if path:
        download_path = path
        path_label.config(text=f"Save to: {download_path}")

# -----------------------------
# Download video
# -----------------------------
def download_video():
    global process
    url = url_entry.get().strip()
    selected = format_dropdown.get()
    if not url or not selected:
        messagebox.showerror("Error", "Missing URL or format.")
        return

    format_id = format_options[selected]

    def run_download():
        global process
        progress_bar["value"] = 0
        status_label.config(text="Downloading...")
        root.update_idletasks()

        try:
            # Use local ffmpeg folder and recode video for full compatibility
            ffmpeg_folder = ffmpeg_path

            process = subprocess.Popen(
                [
                    "yt-dlp",
                    url,
                    "-f", f"{format_id}+bestaudio/best",
                    "--recode-video", "mp4",          # 🔥 ensures proper merge + compatible MP4
                    "--ffmpeg-location", ffmpeg_folder,
                    "-o", os.path.join(download_path, "%(title)s.%(ext)s"),
                    "--newline"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                if "%" in line:
                    try:
                        percent_str = line.split("%")[0].split()[-1]
                        progress = float(percent_str)
                        progress_bar["value"] = progress
                        root.update_idletasks()
                    except:
                        pass

            process.wait()

            if process.returncode == 0:
                progress_bar["value"] = 100
                status_label.config(text="Download Complete!")
                messagebox.showinfo("Success", "Download completed successfully.")
            else:
                status_label.config(text="Download failed or cancelled.")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            status_label.config(text="Download error.")
        finally:
            process = None

    threading.Thread(target=run_download).start()

# -----------------------------
# Cancel download
# -----------------------------
def cancel_download():
    global process
    if process:
        process.terminate()
        process = None
        progress_bar["value"] = 0
        status_label.config(text="Download Cancelled.")

# -----------------------------
# GUI Setup
# -----------------------------
root = tk.Tk()
root.title("Professional YouTube Downloader")
root.geometry("700x720")
root.resizable(False, False)

if not has_ytdlp():
    messagebox.showerror("Error", "yt-dlp is not installed.")
    root.destroy()

tk.Label(root, text="Video URL:", font=("Arial", 12)).pack(pady=5)
url_entry = tk.Entry(root, width=90)
url_entry.pack(pady=5)

tk.Button(root, text="Fetch Video Info", command=fetch_formats).pack(pady=10)

title_label = tk.Label(root, text="", font=("Arial", 13, "bold"), wraplength=650)
title_label.pack(pady=5)

thumbnail_label = tk.Label(root)
thumbnail_label.pack(pady=10)

tk.Label(root, text="Select Quality:", font=("Arial", 11)).pack(pady=5)
format_dropdown = ttk.Combobox(root, width=30, state="readonly")
format_dropdown.pack(pady=5)

tk.Button(root, text="Choose Save Location (Optional)", command=choose_folder).pack(pady=10)
path_label = tk.Label(root, text=f"Save to: {download_path}")
path_label.pack(pady=5)

progress_bar = ttk.Progressbar(root, length=600, mode="determinate")
progress_bar.pack(pady=20)

tk.Button(root, text="Download", width=20, command=download_video).pack(pady=5)
tk.Button(root, text="Cancel Download", width=20, command=cancel_download).pack(pady=5)

status_label = tk.Label(root, text="Ready.", font=("Arial", 11))
status_label.pack(pady=20)

root.mainloop()
