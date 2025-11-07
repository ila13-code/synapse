# Synapse

## Setup rapido

1. Create una copia del file `.env.example` (se presente) oppure create un nuovo `.env` nella root del progetto.
2. Rinominatelo in `.env` e aggiungete le vostre chiavi/config preferite:

```
# LLM remoto (Google Gemini)
GEMINI_API_KEY=la-vostra-api-key
GEMINI_MODEL=gemini-2.0-flash-exp

# LLM locale (LM Studio / Ollama via API OpenAI-like)
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=http://127.0.0.1:1234/v1
LOCAL_LLM_MODEL=

# RAG e Reflection
USE_RAG=true
USE_REFLECTION=true

# Ricerca Web (opzionale ma consigliata)
# Con Tavily evitiamo problemi di rate limiting (es. DuckDuckGo 202)
TAVILY_API_KEY=la-vostra-api-key
```

3. Installazione dipendenze e avvio (Windows PowerShell):

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Note:
- Per usare la ricerca web integrata, impostate `TAVILY_API_KEY`. Se non presente, il codice farà un fallback leggero su Wikipedia.
- Se preferite un LLM locale, avviate LM Studio (o equivalente) e lasciate `USE_LOCAL_LLM=true`.
- Con Gemini impostate `USE_LOCAL_LLM=false` e fornite `GEMINI_API_KEY`.
