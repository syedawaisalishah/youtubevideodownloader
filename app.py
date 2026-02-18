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
        subprocess.run(
            ["yt-dlp", "-h"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
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
    root.update()

    try:
        result = subprocess.run(
            ["yt-dlp", url, "--dump-json"],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)

        # Show title
        title_label.config(text=data.get("title", "Unknown Title"))

        # Load thumbnail
        thumbnail_url = data.get("thumbnail")
        if thumbnail_url:
            response = requests.get(thumbnail_url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img = img.resize((200, 120))
            img = ImageTk.PhotoImage(img)
            thumbnail_label.config(image=img)
            thumbnail_label.image = img

        # Load formats
        formats = data.get("formats", [])
        format_options.clear()
        format_dropdown["values"] = []

        for f in formats:
            if f.get("resolution") and f.get("ext"):
                label = f"{f['format_id']} - {f['resolution']} - {f['ext']}"
                format_options[label] = f["format_id"]

        format_dropdown["values"] = list(format_options.keys())

        if format_options:
            format_dropdown.current(0)
            status_label.config(text="Formats loaded.")
        else:
            status_label.config(text="No formats available.")

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
# Download video with progress
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

        try:
            process = subprocess.Popen(
                [
                    "yt-dlp",
                    url,
                    "-f",
                    format_id,
                    "-o",
                    os.path.join(download_path, "%(title)s.%(ext)s"),
                    "--newline",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True,
            )

            for line in process.stdout:
                if "%" in line:
                    try:
                        percent = line.split("%")[0].split()[-1]
                        progress = float(percent)
                        progress_bar["value"] = progress
                        root.update_idletasks()
                    except:
                        pass

            process.wait()

            if process.returncode == 0:
                status_label.config(text="Download Complete!")
                messagebox.showinfo("Success", "Download completed!")
            else:
                status_label.config(text="Download stopped.")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            status_label.config(text="Error during download.")

    threading.Thread(target=run_download).start()


# -----------------------------
# Cancel download
# -----------------------------
def cancel_download():
    global process
    if process:
        process.terminate()
        status_label.config(text="Download Cancelled.")
        progress_bar["value"] = 0


# -----------------------------
# GUI
# -----------------------------
root = tk.Tk()
root.title("Advanced YouTube Downloader")
root.geometry("600x550")
root.resizable(False, False)

if not has_ytdlp():
    messagebox.showerror("Error", "yt-dlp is not installed.")
    root.destroy()

tk.Label(root, text="Video URL:").pack(pady=5)
url_entry = tk.Entry(root, width=70)
url_entry.pack(pady=5)

tk.Button(root, text="Fetch Video Info", command=fetch_formats).pack(pady=5)

title_label = tk.Label(root, text="", font=("Arial", 12, "bold"), wraplength=500)
title_label.pack(pady=5)

thumbnail_label = tk.Label(root)
thumbnail_label.pack(pady=5)

format_dropdown = ttk.Combobox(root, width=65, state="readonly")
format_dropdown.pack(pady=10)

tk.Button(root, text="Choose Save Location (Optional)", command=choose_folder).pack()

path_label = tk.Label(root, text=f"Save to: {download_path}")
path_label.pack(pady=5)

progress_bar = ttk.Progressbar(root, length=400, mode="determinate")
progress_bar.pack(pady=10)

tk.Button(root, text="Download", command=download_video).pack(pady=5)
tk.Button(root, text="Cancel Download", command=cancel_download).pack(pady=5)

status_label = tk.Label(root, text="Ready.")
status_label.pack(pady=10)

root.mainloop()
