# Synapse

## Link alle slide
https://www.canva.com/design/DAG7ZGP-xUE/9DsrWSF4P4VmKBDHxp55fg/edit?utm_content=DAG7ZGP-xUE&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton

---

## Setup rapido

### 1. Configurazione environment variables

Create un file `.env` nella root del progetto copiando `.env.example`:
```bash
cp .env.example .env
```

Modificate il file `.env` inserendo le vostre API key.

**Note sulla configurazione:**
- **Multiple API Keys**: Il sistema prova automaticamente le API key successive quando una esaurisce i token
- **RAG**: Retrieval-Augmented Generation per risposte contestualizzate
- **Reflection**: Iterazioni multiple per migliorare la qualità delle risposte
- **Tavily**: Web search API per evitare rate limiting

---

### 2. Installazione e avvio (Windows PowerShell)
```powershell
# Crea environment virtuale
python -m venv .venv

# Attiva environment
.\.venv\Scripts\Activate.ps1

# Installa dipendenze
pip install -r requirements.txt

# Avvia l'applicazione
python main.py
```

---

### 3. Configurazioni alternative

#### Uso con LLM locale (Ollama/LM Studio)
```dotenv
USE_LOCAL_LLM=true
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1  # Ollama
# oppure
LOCAL_LLM_BASE_URL=http://127.0.0.1:1234/v1   # LM Studio
```

#### Disabilitare funzionalità opzionali
```dotenv
USE_RAG=false
USE_REFLECTION=false
POWER_USER_MODE=false
```

