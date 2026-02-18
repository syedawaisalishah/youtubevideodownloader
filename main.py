import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import threading

# -----------------------------
# Check if yt-dlp is installed
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
# Fetch available formats
# -----------------------------
def fetch_formats():
    url = url_entry.get().strip()

    if not url:
        messagebox.showerror("Error", "Please enter a video URL.")
        return

    status_label.config(text="Fetching formats...")
    root.update()

    try:
        result = subprocess.run(
            ["yt-dlp", url, "--dump-json"],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)

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

    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Could not fetch formats.\n{e.stderr}")
        status_label.config(text="Error fetching formats.")


# -----------------------------
# Download video
# -----------------------------
def download_video():
    url = url_entry.get().strip()
    selected = format_dropdown.get()

    if not url or not selected:
        messagebox.showerror("Error", "Missing URL or format selection.")
        return

    format_id = format_options[selected]

    def run_download():
        status_label.config(text="Downloading...")
        try:
            subprocess.run(
                ["yt-dlp", url, "-f", format_id],
                check=True
            )
            status_label.config(text="Download complete!")
            messagebox.showinfo("Success", "Download complete!")
        except subprocess.CalledProcessError:
            status_label.config(text="Download failed.")
            messagebox.showerror("Error", "Download failed.")

    threading.Thread(target=run_download).start()


# -----------------------------
# GUI Setup
# -----------------------------
root = tk.Tk()
root.title("YouTube Downloader GUI")
root.geometry("500x250")
root.resizable(False, False)

if not has_ytdlp():
    messagebox.showerror("Error", "yt-dlp is not installed.")
    root.destroy()

format_options = {}

# URL Entry
tk.Label(root, text="Video URL:").pack(pady=5)
url_entry = tk.Entry(root, width=60)
url_entry.pack(pady=5)

# Fetch Button
tk.Button(root, text="Fetch Formats", command=fetch_formats).pack(pady=5)

# Format Dropdown
format_dropdown = ttk.Combobox(root, width=55, state="readonly")
format_dropdown.pack(pady=5)

# Download Button
tk.Button(root, text="Download", command=download_video).pack(pady=10)

# Status Label
status_label = tk.Label(root, text="Ready.")
status_label.pack()

root.mainloop()