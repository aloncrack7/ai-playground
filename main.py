from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agents.orchestrator_agent import LanguageSelectorAgent 

app = FastAPI()

# Serve static assets (css, js, images, etc.)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve index.html at root
@app.get("/")
def read_index():
    return FileResponse("frontend/index.html")

class TextRequest(BaseModel):
    text: str

@app.post("/generate")
def generate(data: TextRequest):
    text = data.text

@app.post("/correct_orthography")
def correct_orthography():
    ...