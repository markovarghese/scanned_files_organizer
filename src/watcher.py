import os
import time
import datetime
import shutil
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

from src.config import SCAN_DIRECTORY, FILE_READY_WAIT_SECONDS
from src.extractor import Extractor
from src.classifier import Classifier

# We only process known extensions
VALID_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png')

class ScanHandler(FileSystemEventHandler):
    def __init__(self):
        self.extractor = Extractor()
        self.classifier = Classifier()
        
    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def process_file(self, file_path):
        # Ignore files not in root folder explicitly to avoid infinite loops when moving
        if os.path.dirname(file_path) != os.path.abspath(SCAN_DIRECTORY):
            return
            
        if not str(file_path).lower().endswith(VALID_EXTENSIONS):
            return

        # Buffer Logic: make sure file is done writing (e.g. from OneDrive)
        if not self._wait_for_file_ready(file_path):
            print(f"[Watcher] File {file_path} might be busy or deleted, skipping.")
            return

        print(f"\n[Watcher] Processing new file: {file_path}")
        
        # 1. Gather dynamic categories
        categories = self._get_dynamic_categories()
        
        # 2. Extract Text
        text = self.extractor.extract_text(file_path)
        
        # 3. Classify and Rename
        category, new_filename, keep_original = self.classifier.determine_classification(file_path, text, categories)
        
        # Python heuristics: Enforce keeping original name if it looks human-generated
        orig_basename = os.path.splitext(os.path.basename(file_path))[0]
        lower_name = orig_basename.lower().strip()
        is_generic = lower_name.startswith(("scan", "img", "image", "doc", "untitled", "unrecognized_file", "unnamed_file"))
        
        # If it has spaces and doesn't start with a generic scanner term, it's a human name!
        if " " in orig_basename and not is_generic:
            keep_original = True
        
        # Get the creation time of the file in UTC
        try:
            create_time = os.path.getctime(file_path)
            dt = datetime.datetime.fromtimestamp(create_time, tz=datetime.timezone.utc)
        except Exception:
            dt = datetime.datetime.now(datetime.timezone.utc)
        timestamp_str = dt.strftime("%Y%m%d%H%M%S")
        
        # Ensure we strip out any accidentally generated extensions from the LLM
        orig_ext = os.path.splitext(file_path)[1]
        
        if keep_original:
            final_filename = os.path.basename(file_path)
        else:
            base_filename = os.path.splitext(new_filename)[0].strip()
            final_filename = f"{base_filename} {timestamp_str}{orig_ext}"
            
        # 4. Move file
        self._move_file(file_path, category, final_filename)

    def _wait_for_file_ready(self, file_path, wait_time=FILE_READY_WAIT_SECONDS):
        """
        Wait until file size doesn't change for `wait_time` seconds,
        meaning it's completely written to disk.
        """
        try:
            prev_size = -1
            time.sleep(wait_time)
            while True:
                if not os.path.exists(file_path):
                    return False
                curr_size = os.path.getsize(file_path)
                if curr_size == prev_size:
                    return True
                prev_size = curr_size
                time.sleep(wait_time)
        except Exception:
            return False

    def _get_dynamic_categories(self) -> list:
        """
        Gets all directories and sub-directories inside the root SCAN_DIRECTORY.
        """
        valid_cats = []
        try:
            for root, dirs, files in os.walk(SCAN_DIRECTORY):
                # Don't include the root folder itself
                if root != SCAN_DIRECTORY:
                    # Get relative path (e.g., 'Employment & Investments\W2')
                    rel_path = os.path.relpath(root, SCAN_DIRECTORY)
                    valid_cats.append(rel_path)
        except Exception as e:
            print(f"[Watcher] Category Error: {e}")
            
        # Optional: sort or filter empty strings
        return valid_cats

    def _move_file(self, src_file: str, category: str, new_filename: str):
        target_dir = os.path.join(SCAN_DIRECTORY, category)
        try:
            os.makedirs(target_dir, exist_ok=True)
            new_path = os.path.join(target_dir, new_filename)
            
            # Handle collision
            count = 1
            base, ext = os.path.splitext(new_filename)
            while os.path.exists(new_path):
                new_path = os.path.join(target_dir, f"{base}_{count}{ext}")
                count += 1
                
            shutil.move(src_file, new_path)
            print(f"[Success] Moved to: {new_path}")
        except Exception as e:
            print(f"[Watcher] Move Error: {e}")

def run_watcher():
    if not os.path.exists(SCAN_DIRECTORY):
        os.makedirs(SCAN_DIRECTORY)
        print(f"Created base directory: {SCAN_DIRECTORY}")
        
    event_handler = ScanHandler()
    
    # Use PollingObserver instead of regular Observer because standard inotify 
    # events do not cross the Windows-to-Docker volume boundary effectively.
    observer = PollingObserver()
    
    observer.schedule(event_handler, SCAN_DIRECTORY, recursive=False)
    observer.start()
    
    print(f"Watching directory: {SCAN_DIRECTORY} for new files...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
