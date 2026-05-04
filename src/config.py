import os
from dotenv import load_dotenv

# Load default .env if it exists
load_dotenv()

# We expect this to be mounted and default to /app/scans
SCAN_DIRECTORY = os.getenv("SCAN_DIRECTORY", "/app/scans")

# Ensure it works for both docker and local run
OLLAMA_HOST = os.getenv("APP_OLLAMA_HOST", "http://host.docker.internal:11434")

# Read models
OLLAMA_TEXT_MODEL = os.getenv("OLLAMA_TEXT_MODEL", "ministral-3:14b")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llama3.2-vision")

# Number of seconds to wait for file writing
FILE_READY_WAIT_SECONDS = int(os.getenv("FILE_READY_WAIT_SECONDS", 5))

# Number of seconds to wait for Ollama response
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", 300))

# Fallback category if LLM cannot determine it
MISC_FOLDER_NAME = "Miscellaneous"
