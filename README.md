# Auto Scan Organizer

This repository contains a Python-based Docker application that continuously watches a `Scans` directory (e.g. hooked up to your Microsoft OneDrive) and leverages a local Ollama Large Language Model to organize and intelligently rename your files. 

It handles both standard text documents (PDF/JPEG) and image-heavy files (e.g., family photos).

## Architecture overview
- **Text Documents:** The program runs Optical Character Recognition (OCR) locally via Tesseract on the first two pages to extract text context, then sends that text to `ministral-3:14b` natively in Ollama.
- **Photos/Images:** If you drop in an image file and no text is found, it will automatically connect to a Vision LLM (`llama3.2-vision`) to describe the photo and appropriately organize it. 

## Requirements
- Docker
- Local Ollama running with the `ministral-3:14b` model installed.
- (Optional but Highly Recommended for Photos): The `llama3.2-vision` model.

### 1. Install fallback Vision model in Ollama
Since `ministral-3` is a robust text model but lacks native vision, this application uses a secondary lightweight vision model for pure images. Run this command on your host:
```bash
ollama pull llama3.2-vision
```

### 2. Configure Environment
A `.env.example` file is included. By default, it runs with host network defaults.
- Copy `.env.example` to `.env`.
- Ensure `HOST_SCAN_DIR` in your `.env` file accurately matches your root Windows path for Scans.

### 3. Build and Run
From the root of this repository, run:
```bash
docker-compose build
docker-compose up -d
```
You can view real-time logs using:
```bash
docker-compose logs -f
```

## How It Categorizes
The application will scan all subdirectories inside your base Scans folder and dynamically provide those as options to the LLM. 
For example, if you place a file into your OneDrive Scans folder root, and the folders `Employment -> W2` exist, it will move standard tax documents immediately into `Employment/W2`. If it cannot determine a match, it puts the file into `Miscellaneous`.

## How It Renames Files
The app contains sophisticated rules for renaming:
1. **Human-Named Override:** If your original file name contains spaces and doesn't start with generic scanner templates (e.g. `$200 gift card from Molly Aunty NY.pdf`), the Python Watcher locks it in. It will correctly categorize it via AI, but *will not touch your manual filename.*
2. **Generates from Context:** For generic filenames like `scan123.pdf`, the AI summarizes the contents into a new, concise descriptive string.
3. **Tax Document Structuring:** If the AI detects it is a tax document, it strictly overrides the name into the format `Form <ID> <Year> <Description>`.
4. **Timestamp Suffixes:** Any file that is renamed by the AI is automatically suffixed with its exact Windows filesystem creation time (in UTC) formatted as `YYYYMMDDHHMMSS` to ensure zero file-collisions forever.
