from enum import Enum

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