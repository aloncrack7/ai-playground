# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the server
uvicorn main:app --reload

# Run on a specific port
uvicorn main:app --reload --port 8001
```

Requires Ollama running locally at `localhost:11434` for local models (Llama 3.8B, Gemma 3.4B). API keys for OpenAI and Google Gemini go in a `.env` file.

## Architecture

This is a FastAPI + LangGraph multi-agent text assistant. The frontend is vanilla JS served as static files from `/static`.

**Request flow:**
```
HTTP POST → main.py → Orchestrator (LangGraph) → specialized Agent (LangGraph) → LLM
```

**Two modes:**
- `generation` — continues text via `GenerationAgent` (single-node graph)
- `orthography` — corrects spelling/grammar via `OrchestratorAgent` → `OrthographyAgent`

### Key files

- `main.py` — FastAPI app with three endpoints: `POST /set_model`, `POST /generate`, `POST /correct_orthography`
- `commun.py` — `Models` enum + `get_model_from_enum()` factory; the single place to swap LLM providers
- `agents/orchestrator_agent.py` — coordinates language detection → (optional translation) → orthography check
- `agents/orthography_agent.py` — runs correction, then `_word_level_diff()` to produce structured diffs
- `agents/generation_agent.py` — single-node graph that continues text
- `utils.py` — `check_ollama_is_running()`, `load_languages()` (scans `promts/translations/` for cached language prompts)

### Multi-language support

The orchestrator detects language (ISO 639-1 code), then checks whether an orthography prompt for that language already exists in `promts/translations/orthography_promt_{lang}.md`. If not, it uses `promts/translator_promt.md` to translate the base English prompt and caches it there. New languages are supported automatically once the translation is cached.

### Frontend diff interface

`frontend/js/app.js` receives the diff array `[{original, correction, start, end}]` from `/correct_orthography` and renders an interactive overlay where each change can be individually accepted (✓) or denied (✗). `buildFinalText()` reconstructs the final string from user decisions.

### Structured output

All agents use Pydantic models with LangChain's `.with_structured_output()` for reliable JSON parsing from LLMs.
