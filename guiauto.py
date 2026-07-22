import tkinter as tk
from tkinter import scrolledtext
import time
import os
import boto3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


WATCH_DIRECTORY = "./upload_watch_zone"
S3_BUCKET_NAME = "minor-project-raw-ingress-2026"


s3_client = boto3.client('s3')

class UI_EventHandler(FileSystemEventHandler):
    
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)
        VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')

        if not filename.lower().endswith(VALID_EXTENSIONS):
            return

        self.log_callback(f"\n[+] New image detected: {filename}")
        time.sleep(1) 

        try:
            self.log_callback(f"    Uploading to S3...")
            s3_client.upload_file(filepath, S3_BUCKET_NAME, filename)
            self.log_callback(f"    Upload complete! Lambda triggered.")
        except Exception as e:
            self.log_callback(f"    [!] Error uploading: {e}")

class AutoUploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AWS Cloud Pipeline - Auto Uploader")
        self.root.geometry("550x450")
        self.root.configure(padx=20, pady=20)

        self.observer = None

        
        
        self.status_label = tk.Label(root, text="Status: OFFLINE", font=("Helvetica", 16, "bold"), fg="red")
        self.status_label.pack(pady=(0, 15))

        self.start_btn = tk.Button(root, text="▶ Start Watching Folder", command=self.start_watching, 
                                   bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"), width=25, pady=5)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="■ Stop Watching", command=self.stop_watching, 
                                  bg="#f44336", fg="white", font=("Helvetica", 12, "bold"), width=25, pady=5, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

        tk.Label(root, text="System Logs:", font=("Helvetica", 10)).pack(anchor="w", pady=(15, 0))
        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=12, font=("Consolas", 9), bg="#1e1e1e", fg="#00ff00")
        self.log_area.pack(pady=5)
        
        self.log("System initialized. Ready to connect to AWS.")

    def log(self, message):
        """Helper function to print text to the GUI text box instead of the terminal"""
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END) 

    def start_watching(self):
        
        if not os.path.exists(WATCH_DIRECTORY):
            os.makedirs(WATCH_DIRECTORY)

        event_handler = UI_EventHandler(self.log)
        self.observer = Observer()
        self.observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
        self.observer.start()

        self.status_label.config(text="Status: LIVE & WATCHING", fg="#4CAF50")
        self.start_btn.config(state=tk.DISABLED, bg="#a5d6a7")
        self.stop_btn.config(state=tk.NORMAL, bg="#f44336")
        self.log(f"[*] Started watching: {WATCH_DIRECTORY}")

    def stop_watching(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        self.status_label.config(text="Status: OFFLINE", fg="red")
        self.start_btn.config(state=tk.NORMAL, bg="#4CAF50")
        self.stop_btn.config(state=tk.DISABLED, bg="#ef9a9a")
        self.log("[*] Engine stopped. No longer watching folder.")


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoUploaderApp(root)
    root.mainloop() 