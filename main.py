import os
from src.watcher import run_watcher

def main():
    print("Starting Auto Scan Organizer...")
    
    # We can check some basic constraints before running
    # but watcher.py does the heavy lifting
    run_watcher()

if __name__ == "__main__":
    main()
