from commun import Models
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from utils import (
    OLLAMA_URL,
    check_ollama_is_running
)
from commun import (
    Models
)

with open("./promts/language_selector_promt.md", "r", encoding="utf-8") as file:
    language_selector_promt = file.read()

class GraphState(dict):
    text: str
    result: str

class Orchestrator:
    def __init__(self):
        if check_ollama_is_running():
            self.model = ChatOllama(
                model=Models.LLAMA.value,
                temperature=0,
                base_url=OLLAMA_URL
            )
        else:
            self.model = ChatOpenAI(
                model=Models.OPEN_AI.value,
                temperature=0
            )

        builder = StateGraph(GraphState)
        
        builder.add_node("check_language", self.check_languge_node)
        builder.set_entry_point("check_language")
        builder.add_edge("check_language", END)

        self.orchestrator = builder.compile()

    def check_languge_node(self, state):
        text = state["text"]

        messages = [
            SystemMessage(content=language_selector_promt),
            HumanMessage(content=text)
        ]

        response = self.model.invoke(messages)

        return {"result": response.content}
    
    def run(self, text: str):
        return self.orchestrator.invoke({"text": text})