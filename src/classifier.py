import json
import base64
import requests
from typing import List, Dict, Tuple
from src.config import OLLAMA_HOST, OLLAMA_TEXT_MODEL, OLLAMA_VISION_MODEL, MISC_FOLDER_NAME

class Classifier:
    def __init__(self):
        self.api_url = f"{OLLAMA_HOST.rstrip('/')}/api/generate"

    def determine_classification(self, file_path: str, extracted_text: str, categories: List[str]) -> Tuple[str, str, bool]:
        """
        Takes extracted text (and potentially the image file path if it's a photo),
        and returns (category, new_filename).
        """
        is_photo = False
        words = extracted_text.split()
        
        # If the file is an image and has very few words, assume it's a photo
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png')) and len(words) < 5:
            is_photo = True
            
        system_prompt = self._build_prompt(file_path, categories)
        
        if is_photo:
            return self._run_vision_model(file_path, system_prompt)
        else:
            return self._run_text_model(extracted_text, system_prompt)

    def _build_prompt(self, file_path: str, categories: List[str]) -> str:
        import os
        orig_name = os.path.basename(file_path)
        cat_list = ", ".join([f'"{c}"' for c in categories])
        prompt = (
            "You are an AI assistant that organizes files. "
            "Examine the document's content (or photo). "
            f"You MUST choose exactly ONE category from the following list: {cat_list}. "
            f"If none fit, or the list is empty, choose '{MISC_FOLDER_NAME}'. "
            "You MUST also generate a descriptive filename for this file based on its content. "
            "DO NOT include a file extension (like .pdf or .jpg). "
            "If the document is a tax form, the filename MUST follow this exact format: 'Form <Tax document form number or id> <Tax Year that the form is for> <description>'. "
            "For example: 'Form 1040 2023 Tax Return' or 'Form W-2 2023 Wage Statement'. "
            "For non-tax documents, simply provide a concise description. "
            f"\nCRITICAL RULE: The original filename is '{orig_name}'. You must evaluate this existing filename EVEN IF the document text is empty, sparse, or unreadable! "
            "If the original filename contains real descriptive words that identify the document (e.g., '$200 gift card from Molly Aunty NY.pdf', 'Graebel claims cheque.pdf', '2022 Tax Return.pdf'), set 'keep_original_name' to true. "
            "If it is generic like 'scan123.pdf', or 'IMG456.jpg', set it to false. "
            "Return ONLY a raw JSON object with keys 'category' (string), 'filename' (string), and 'keep_original_name' (boolean)."
        )
        return prompt

    def _run_text_model(self, text: str, system_prompt: str) -> Tuple[str, str, bool]:
        prompt = f"{system_prompt}\n\nDocument Text:\n{text[:4000]}" # Cap to save context window
        
        payload = {
            "model": OLLAMA_TEXT_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        return self._post_to_ollama(payload)

    def _run_vision_model(self, file_path: str, system_prompt: str) -> Tuple[str, str, bool]:
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        payload = {
            "model": OLLAMA_VISION_MODEL,
            "prompt": system_prompt + "\nDescribe the uploaded photo and categorize it.",
            "images": [encoded_string],
            "stream": False,
            "format": "json"
        }
        return self._post_to_ollama(payload)

    def _post_to_ollama(self, payload: Dict) -> Tuple[str, str, bool]:
        try:
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "{}")
            
            # Parse json
            parsed = json.loads(response_text)
            print(f"[Classifier] LLM Raw JSON Parsing: {parsed}")
            
            category = parsed.get("category", MISC_FOLDER_NAME)
            filename = parsed.get("filename", "unnamed_file")
            
            raw_keep = parsed.get("keep_original_name", False)
            if isinstance(raw_keep, str):
                keep_orig = raw_keep.lower() == "true"
            else:
                keep_orig = bool(raw_keep)
            
            return category, filename, keep_orig
        except Exception as e:
            print(f"[Classifier] LLM Error: {e}")
            return MISC_FOLDER_NAME, "unrecognized_file", False
