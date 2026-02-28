from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agents.orchestrator_agent import Orchestrator 
from commun import Models, str_to_model
import logging
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.INFO, filename="app.log", format="%(asctime)s - %(levelname)s - %(message)s")

# Serve static assets (css, js, images, etc.)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

orchestrator_agent: Orchestrator = None

# Serve index.html at root
@app.get("/")
async def read_index():
    return FileResponse("frontend/index.html")

class TextRequest(BaseModel):
    text: str

@app.post("/set_model")
async def set_model(model: str):
    model_enum = str_to_model(model)

    if model_enum is None:
        return {"status": "error", "message": f"Invalid model name: {model}"}

    global orchestrator_agent
    orchestrator_agent = Orchestrator(model=model_enum)

    return {"status": "ok"}

@app.post("/generate")
async def generate(data: TextRequest):
    text = data.text

@app.post("/correct_orthography")
async def correct_orthography(data: TextRequest):
    global orchestrator_agent
    if orchestrator_agent is None:
        orchestrator_agent = Orchestrator(model=Models.LLAMA)
    result = orchestrator_agent.invoke(data.text, mode="orthography")
    return {"diff": result["diff"], "corrected_text": result["new_text"]}