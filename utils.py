from typing import Dict, List

import requests
from dotenv import load_dotenv
import os
import re

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")

def check_ollama_is_running():
    try:
        response = requests.get(OLLAMA_URL)
        return response.status_code==200
    except requests.exceptions.RequestException:
        return False
    
def load_languages():
    languages: List[str] = []

    files = os.listdir("./promts/translations")
    for file in files:
        file_name = os.path.splitext(file)[0]
        print(file_name)
        language = re.search(r"_(\w{2})$", file_name)
        if language:
             languages.append(language.group(1))
    
    return languages