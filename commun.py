from enum import Enum

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from utils import OLLAMA_URL

class Models(Enum):
    OPEN_AI = "gpt-4.1-mini"
    GEMINI = "gemini-2.5-flash"
    GEMMA = "gemma3:4b"
    LLAMA = "llama3:8b"

def str_to_model(value: str) -> Models | None:
    try:
        return Models(value)
    except ValueError:
        return None
    
def get_model_from_enum(model: Models, temperature: int = 0):
    if model == Models.LLAMA:
        return ChatOllama(
            model=Models.LLAMA.value,
            temperature=temperature,
            base_url=OLLAMA_URL
        )
    elif model == Models.OPEN_AI:
        return ChatOpenAI(
            model=Models.OPEN_AI.value,
            temperature=temperature
        )
    elif model == Models.GEMINI:
        return ChatGoogleGenerativeAI(
            model=Models.GEMINI.value,
            temperature=temperature
        )
    else:
        return ChatOllama(
            model=Models.GEMMA.value,
            temperature=temperature,
            base_url=OLLAMA_URL
        )