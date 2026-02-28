import json
from typing import List
from pydantic import BaseModel
from commun import Models
from agents.orthography_agent import OrthographyAgent
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from utils import (
    OLLAMA_URL,
    check_ollama_is_running,
    load_languages
)
from commun import (
    Models
)

class GraphState(dict):
    text: str
    language: str
    mode: str
    new_text: str
    diff: List[str]

class TranslationOutput(BaseModel):
    translation: str

class Orchestrator:
    def __init__(self, model = Models.LLAMA):
        if model == Models.LLAMA:
            self.model = ChatOllama(
                model=Models.LLAMA.value,
                temperature=0,
                base_url=OLLAMA_URL
            )
        elif model == Models.OPEN_AI:
            self.model = ChatOpenAI(
                model=Models.OPEN_AI.value,
                temperature=0
            )
        elif model == Models.GEMINI:
            self.model = ChatGoogleGenerativeAI(
                model=Models.GEMINI.value,
                temperature=0
            )
        else:
            self.model = ChatOllama(
                model=Models.GEMMA.value,
                temperature=0,
                base_url=OLLAMA_URL
            )
        
        with open("./promts/language_selector_promt.md", "r", encoding="utf-8") as file:
            self.LANGUAGE_SELECTOR_PROMT = file.read()
        with open("./promts/translator_promt.md", "r", encoding="utf-8") as file:
            self.TRANSLATOR_PROMT = file.read()
        with open("./promts/orthography_promt.md", "r", encoding="utf-8") as file:
            self.OTRHOGRAPHY_PROMT = file.read()


        self.languages = load_languages()

        self.orthography_agent = OrthographyAgent(self.model)

        builder = StateGraph(GraphState)
        builder.add_node("check_language", self.check_languge_node)
        builder.add_node("translate_node", self.translate)
        builder.add_node("orthography_node", self.check_orthography_node)

        builder.set_entry_point("check_language")
        builder.add_conditional_edges(
            "check_language",
            self.is_translated,
            {
                True: "orthography_node",
                False: "translate_node"
            }
        )
        builder.add_edge("translate_node", "orthography_node")
        builder.add_edge("orthography_node", END)

        self.orchestrator = builder.compile()

    def check_languge_node(self, state):
        text = state["text"]

        messages = [
            SystemMessage(content=self.LANGUAGE_SELECTOR_PROMT),
            HumanMessage(content=text)
        ]

        response = self.model.invoke(messages)

        return {"language": response.content}
    
    def is_translated(self, state):
        return state["language"] in self.languages
    
    def translate(self, state):
        user_promt = f"Translate into {state['language']} teh following text: {self.OTRHOGRAPHY_PROMT}."

        messages = [
            SystemMessage(content=self.TRANSLATOR_PROMT),
            HumanMessage(user_promt)
        ]

        translation_structured_model = self.model.with_structured_output(TranslationOutput)
        response = translation_structured_model.invoke(messages)

        self.languages[state["language"]] = f"./promts/translations/orthography_promt_{state['language']}.md"

        new_text = response.translation

        with open(self.languages[state["language"]], "w", encoding="utf-8") as file:
            file.write(new_text)

        return {}
    
    def check_orthography_node(self, state):
        result = self.orthography_agent.invoke(state["text"], state["language"])
        return {"diff": result["differences"], "new_text": result["corrected_text"]}
    
    def invoke(self, text: str, mode: str = "orthography"):
        # Only orthography mode is supported for now
        return self.orchestrator.invoke({"text": text, "mode": mode})