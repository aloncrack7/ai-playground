import requests
from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")

def check_ollama_is_running():
    try:
        response = requests.get(OLLAMA_URL)
        return response.status_code==200
    except requests.exceptions.RequestException:
        return False