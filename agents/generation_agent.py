from typing import Optional

from langchain.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from commun import Models, get_model_from_enum

with open("./promts/generation_promt.md", "r", encoding="utf-8") as f:
    GENERATION_PROMT = f.read()

class GeneratorState(BaseModel):
    input: str
    output: Optional[str]

class GenerationOutput(BaseModel):
    generated_text: str

class GeneratorAgent:
    def __init__(self, model_name: Models):
        self.model = get_model_from_enum(model_name, temperature=0.4)
        self.model = self.model.with_structured_output(GenerationOutput)

        self.builder = StateGraph(GeneratorState)

        self.builder.add_node("generate", self.generate)

        self.builder.set_entry_point("generate")
        self.builder.add_edge("generate", END)

        self.graph = self.builder.compile()

    def generate(self, state: GeneratorState):
        human_message = state.input

        messages = [
            HumanMessage(content=human_message),
            SystemMessage(content=GENERATION_PROMT)
        ]

        response = self.model.invoke(messages)

        return {"output": response.generated_text}

    def invoke(self, text: str) -> str:
        return self.graph.invoke({"input": text, "output": None})