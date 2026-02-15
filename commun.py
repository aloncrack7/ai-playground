from enum import Enum

class Models(Enum):
    OPEN_AI = "gpt-4.1-mini"
    GEMINI = "gemini-2.5-flash"
    GEMMA = "gemma3:4b"
    LLAMA = "llama3:8b"