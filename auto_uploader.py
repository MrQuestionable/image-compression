import time
import os
import boto3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIRECTORY ="C:\\Users\\khand\\OneDrive\\Documents\\coding\\project\\uploadwatchzone"
S3_BUCKET_NAME = "minor-project-raw-ingress-2026" # 

s3_client = boto3.client('s3')

class NewImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        
        if event.is_directory:
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)

        
        VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')

        
        if not filename.lower().endswith(VALID_EXTENSIONS):
            return 

        print(f"\n[+] New image detected: {filename}")
        
        
        time.sleep(1) 

        try:
            print(f"    Uploading '{filename}' to S3 bucket '{S3_BUCKET_NAME}'...")
            
            
            s3_client.upload_file(filepath, S3_BUCKET_NAME, filename)
            
            print(f"    Upload complete! AWS Lambda should trigger momentarily.")
        except Exception as e:
            print(f"    [!] Error uploading {filename}: {e}")

if __name__ == "__main__":
    
    if not os.path.exists(WATCH_DIRECTORY):
        os.makedirs(WATCH_DIRECTORY)
        print(f"Created directory: {WATCH_DIRECTORY}")

    event_handler = NewImageHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    
    print(f"[*] Starting automatic uploader...")
    print(f"[*] Watching folder: '{WATCH_DIRECTORY}'")
    print("[*] Press Ctrl+C to stop.")
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping automatic uploader...")
        observer.stop()
        
    observer.join()