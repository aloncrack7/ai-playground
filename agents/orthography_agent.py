import re
from typing import List, Dict, Any

from pydantic import BaseModel, Field
from commun import Models
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
import difflib
from utils import (
    OLLAMA_URL
)
from commun import (
    Models
)


def _get_word_spans(text: str) -> List[tuple]:
    """Return list of (word, start, end) for each word in text."""
    spans = []
    for m in re.finditer(r'\S+', text):
        spans.append((m.group(), m.start(), m.end()))
    return spans


def _word_level_diff(original: str, corrected: str) -> List[Dict[str, Any]]:
    """Compute word-level differences with character positions. Returns list of
    {"original": str, "correction": str, "start": int, "end": int} for each change.
    """
    orig_spans = _get_word_spans(original)
    corr_spans = _get_word_spans(corrected)
    orig_words = [s[0] for s in orig_spans]
    corr_words = [s[0] for s in corr_spans]

    matcher = difflib.SequenceMatcher(None, orig_words, corr_words)
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            orig_part = ' '.join(orig_words[i1:i2])
            corr_part = ' '.join(corr_words[j1:j2])
            # Use span of the first and last word in the range
            start = orig_spans[i1][1]
            end = orig_spans[i2 - 1][2]
            changes.append({
                "original": orig_part,
                "correction": corr_part,
                "start": start,
                "end": end
            })
        elif tag == 'delete':
            orig_part = ' '.join(orig_words[i1:i2])
            start = orig_spans[i1][1]
            end = orig_spans[i2 - 1][2]
            changes.append({
                "original": orig_part,
                "correction": "",
                "start": start,
                "end": end
            })
        elif tag == 'insert':
            corr_part = ' '.join(corr_words[j1:j2])
            # Insert after the word before, or at start
            insert_after = orig_spans[i1 - 1][2] if i1 > 0 else 0
            changes.append({
                "original": "",
                "correction": corr_part,
                "start": insert_after,
                "end": insert_after
            })
    return sorted(changes, key=lambda c: c["start"])

class OrthographyOutput(BaseModel):
    corrected_text: str

class OrthographyStatus(BaseModel):
    original_text: str 
    language: str
    corrected_text: str | None = None
    differences: List[str] | None = None

class OrthographyAgent:
    def __init__(self, model):
        self.model = model
        builder = StateGraph(OrthographyStatus)

        builder.add_node("check_orthography", self.check_orthography_node)
        builder.add_node("get_differences", self.get_differences_node)

        builder.set_entry_point("check_orthography")
        builder.add_edge("check_orthography", "get_differences")
        builder.add_edge("get_differences", END)

        self.orchestrator = builder.compile()
         
        self.model = self.model.with_structured_output(OrthographyOutput)

    def check_orthography_node(self, state: OrthographyStatus):
        text = state.original_text
        language = state.language
        with open(f"./promts/translations/orthography_promt_{language}.md", "r", encoding="utf-8") as file:
            ORTHOGRAPHY_PROMT = file.read()

        messages = [
            SystemMessage(content=ORTHOGRAPHY_PROMT),
            HumanMessage(content=text)
        ]

        response = self.model.invoke(messages)

        return {"corrected_text": response.corrected_text}
    
    def get_differences_node(self, state: OrthographyStatus):
        diff = _word_level_diff(state.original_text, state.corrected_text)
        return {"differences": diff}
    
    def invoke(self, input_text, language):
        result = self.orchestrator.invoke({"original_text": input_text, "language": language})
        return {"differences": result["differences"], "corrected_text": result["corrected_text"]}