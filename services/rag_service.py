# rag_service.py
"""
Servizio RAG (Retrieval-Augmented Generation) con ChromaDB e embedding dinamici
(Ollama oppure Gemini) scelti via .env
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import chromadb
import requests
from chromadb.config import Settings
from google import genai


# ==========================
#   EMBEDDING FUNCTIONS
# ==========================
class OllamaEmbeddingFunction:
    def __init__(self, base_url: str = "http://127.0.0.1:11434/v1",
                 model: str = "nomic-embed-text:latest",
                 api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

    def name(self) -> str:
        return "ollama-openai-compat-embeddings"

    def version(self) -> str:
        return "1.0.0"
    
    def embed_query(self, input):
        """Metodo per embedding di una singola query.
        ChromaDB si aspetta che questo metodo restituisca una LISTA DI VETTORI (List[List[float]]).
        """
        # result è già List[List[float]]
        result = self.__call__([input] if isinstance(input, str) else input) 
        if not result:
            return []
        
        # Restituisci direttamente il risultato di __call__
        return result

    def __call__(self, input):  # firma richiesta da Chroma
        if isinstance(input, str):
            texts = [input]
        else:
            texts = list(input)

        resp = requests.post(
            f"{self.base_url}/embeddings",
            headers=self._headers,
            json={"model": self.model_name, "input": texts},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = [item.get("embedding") for item in data.get("data", [])]
        # Normalizza ad una matrice List[List[float]]
        out = []
        for emb in embeddings:
            if emb is None:
                continue
            try:
                out.append([float(x) for x in emb])
            except Exception:
                # Se l'API cambia formato, prova a pescare da chiave "values"
                vals = emb.get("values") if isinstance(emb, dict) else None
                out.append([float(x) for x in (vals or [])])
        return out

    # Alcune versioni di Chroma chiamano esplicitamente questo metodo
    def embed_documents(self, inputs: List[str]) -> List[List[float]]:
        return self.__call__(inputs)


# SOSTITUISCI L'INTERA CLASSE CON QUESTA:

class GeminiEmbeddingFunction:
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        
        # Correzione 1: Aggiungi 'models/' se non è già presente
        if not model.startswith("models/"):
            self.model_name = f"models/{model}"
        else:
            self.model_name = model

    def name(self) -> str:
        return "gemini-embeddings"

    def version(self) -> str:
        return "1.0.0"
    
    def embed_query(self, input):
        """Metodo per embedding di una singola query.
        ChromaDB si aspetta che questo metodo restituisca una LISTA DI VETTORI (List[List[float]]).
        """
        # __call__ restituisce già List[List[float]], che è la forma richiesta
        # (es. [[0.1, 0.2, ...]])
        result = self.__call__([input] if isinstance(input, str) else input)
        if not result:
            return []
        return result

    def __call__(self, input):
        print("[DEBUG] (rag_service) Avvio __call__ di GeminiEmbeddingFunction.")
        
        if isinstance(input, str):
            texts = [input]
        else:
            texts = list(input)
        
        original_texts_count = len(texts)
        if original_texts_count == 0:
             print("[DEBUG] (rag_service) Ricevuto input vuoto. Ritorno.")
             return []

        # --- NUOVA AGGIUNTA: Filtra stringhe vuote ---
        # L'API di Gemini non accetta stringhe vuote.
        # Creiamo una mappa: {indice_originale: testo_valido}
        valid_texts_map = {}
        for i, text in enumerate(texts):
            if text and text.strip(): # Controlla che non sia None, "" o solo spazi
                valid_texts_map[i] = text
        
        # Lista di soli testi validi da inviare all'API
        batchable_texts = list(valid_texts_map.values())
        
        if not batchable_texts:
            print("[DEBUG] (rag_service) Nessun testo valido (solo stringhe vuote). Ritorno vettori di zeri.")
            embedding_dim = 768 # Default per text-embedding-004
            return [[0.0] * embedding_dim] * original_texts_count

        print(f"[DEBUG] (rag_service) Testi originali: {original_texts_count}, Testi validi da inviare: {len(batchable_texts)}")
        
        MAX_BATCH_SIZE = 100
        # Dizionario per contenere i risultati, mappati sull'indice dei *testi validi*
        valid_embeddings_map = {} 
        
        try:
            for i in range(0, len(batchable_texts), MAX_BATCH_SIZE):
                batch_texts = batchable_texts[i:i + MAX_BATCH_SIZE]
                
                print(f"[DEBUG] (rag_service) Invio batch {i//MAX_BATCH_SIZE + 1} con {len(batch_texts)} chunk all'API...")
                
                # --- CHIAMATA API ---
                # Supporta sia batch che singolo a seconda della versione di google-genai
                res = None
                try:
                    # API batch (preferita)
                    res = self.client.models.embed_content(
                        model=self.model_name,
                        contents=batch_texts,
                    )
                except Exception:
                    # Fallback: chiama per ogni item (più lento, ma robusto)
                    batch_embeddings = []
                    for t in batch_texts:
                        single = self.client.models.embed_content(
                            model=self.model_name,
                            content=t,
                        )
                        # normalizza risultato singolo
                        emb_obj = getattr(single, "embedding", None)
                        values = getattr(emb_obj, "values", None) if emb_obj is not None else None
                        if values is None and isinstance(single, dict):
                            values = single.get("embedding", {}).get("values")
                        batch_embeddings.append([float(x) for x in (values or [])])
                    # Salva direttamente in mappa come se fosse risposta batch
                    for j, emb in enumerate(batch_embeddings):
                        original_valid_index = i + j
                        valid_embeddings_map[original_valid_index] = emb
                    print(f"[DEBUG] (rag_service) Batch {i//MAX_BATCH_SIZE + 1} ricevuto (fallback per-item).")
                    continue
                # --- FINE CHIAMATA API ---
                
                print(f"[DEBUG] (rag_service) Batch {i//MAX_BATCH_SIZE + 1} ricevuto.")
                
                # Normalizza formati possibili:
                embeddings_attr = getattr(res, "embeddings", None)
                if embeddings_attr is None:
                    # alcune versioni restituiscono "embedding" al singolare
                    emb_obj = getattr(res, "embedding", None)
                    embeddings_attr = [emb_obj] if emb_obj is not None else []
                batch_embeddings = []
                for e in embeddings_attr:
                    if e is None:
                        batch_embeddings.append(None)
                        continue
                    values = getattr(e, "values", None)
                    if values is None and isinstance(e, dict):
                        values = e.get("values")
                    if values is None and isinstance(e, (list, tuple)):
                        values = e
                    if values is None:
                        batch_embeddings.append(None)
                    else:
                        batch_embeddings.append([float(x) for x in values])
                
                for j, emb in enumerate(batch_embeddings):
                    original_valid_index = i + j
                    valid_embeddings_map[original_valid_index] = emb

        except Exception as e:
            print("======================================================")
            print(f"ERRORE API CRITICO in GeminiEmbeddingFunction.__call__: {e}")
            import traceback
            traceback.print_exc()
            print("======================================================")
            # La logica sotto gestirà i 'None'
        
        print("[DEBUG] (rag_service) API calls completate. Ricostruzione lista embedding...")

        # --- Ricostruzione della lista finale ---
        # Dobbiamo restituire una lista della stessa dimensione dell'input *originale*
        embedding_dim = 768  # Default
        for emb in valid_embeddings_map.values():
            if emb is not None:
                embedding_dim = len(emb)
                break

        zero_vector = [0.0] * embedding_dim
        final_embeddings = []

        # Mappa per indice: {indice_valido_originale : embedding}
        reconstructed_map = {}
        valid_indices_list = list(valid_texts_map.keys())

        for i, emb in valid_embeddings_map.items():
            original_index = valid_indices_list[i]
            reconstructed_map[original_index] = emb

        for i in range(original_texts_count):
            # Cerca l'embedding per l'indice originale 'i'
            emb = reconstructed_map.get(i)

            if emb is not None:
                final_embeddings.append(emb)
            else:
                # Questo era un testo vuoto O l'API ha fallito
                final_embeddings.append(zero_vector)

        print(f"[DEBUG] (rag_service) Ricostruzione completata. Input: {original_texts_count}, Output: {len(final_embeddings)}")
        # Assicura forma 2D: List[List[float]]
        if final_embeddings and isinstance(final_embeddings[0], (int, float)):
            return [[float(x) for x in final_embeddings]]
        return final_embeddings

    # Alcune versioni di Chroma chiamano esplicitamente questo metodo
    def embed_documents(self, inputs: List[str]) -> List[List[float]]:
        return self.__call__(inputs)



# ==========================
#        RAG SERVICE
# ==========================

class RAGService:
    """Servizio per implementare RAG con ChromaDB."""

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Args:
            persist_directory: Directory dove salvare il DB vettoriale
        """
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # --- MODIFICA ---
        # NON creiamo più l'embedder qui. Salviamo solo la configurazione.
        self.use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
        
        if self.use_local_llm:
            self.local_base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
            self.local_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
        else:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not self.gemini_api_key:
                print("ATTENZIONE: GEMINI_API_KEY non trovata. L'embedding fallirà se USE_LOCAL_LLM=false.")
            # Forziamo il modello corretto (hotfix)
            self.gemini_embed_model = "text-embedding-004"

    def _create_embedding_function(self):
        """Sceglie e *crea* l'embedder in base alle variabili d'ambiente.
        Questa funzione DEVE essere chiamata dal thread che la userà.
        """
        if self.use_local_llm:
            print(f"[RAG] Creazione provider (thread-safe): Ollama ({self.local_model})")
            return OllamaEmbeddingFunction(base_url=self.local_base_url, model=self.local_model)
        else:
            if not self.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY non impostata e USE_LOCAL_LLM=false")
            
            print(f"[RAG] Creazione provider (thread-safe): Gemini ({self.gemini_embed_model})")
            return GeminiEmbeddingFunction(api_key=self.gemini_api_key, model=self.gemini_embed_model)
        
    def _load_embedding_function(self):
        """Sceglie automaticamente l'embedder in base alle variabili d'ambiente."""
        use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"

        if use_local_llm:
            base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
            model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
            print(f"[RAG] Embedding provider: Ollama ({model})")
            return OllamaEmbeddingFunction(base_url=base_url, model=model)
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY non impostata e USE_LOCAL_LLM=false")
            
            # Hotfix per forzare il modello corretto:
            embed_model = "text-embedding-004" 
            
            print(f"[RAG] Embedding provider: Gemini ({embed_model})")
            return GeminiEmbeddingFunction(api_key=api_key, model=embed_model)

    def _get_client(self) -> chromadb.Client:
        """Client Chroma per-thread (thread-safe se creato per ogni thread)."""
        return chromadb.Client(Settings(
            persist_directory=self.persist_directory,
            anonymized_telemetry=False
        ))

    def _collection_name(self, subject_id: int, subject_name: str) -> str:
        return f"subject_{subject_id}_{subject_name.lower().replace(' ', '_')}"

    def create_collection(self, subject_id: int, subject_name: str) -> chromadb.Collection:
        """Crea/ottiene la collection per una materia, con embedding function configurata."""
        client = self._get_client()
        return client.get_or_create_collection(
            name=self._collection_name(subject_id, subject_name),
            metadata={"subject_id": subject_id, "subject_name": subject_name},
            embedding_function=self._create_embedding_function() # <-- MODIFICA CHIAVE
        )
    # ------------------ Chunking ------------------

    def chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """
        Divide il testo in chunk più grandi per estrarre più informazioni.
        Aumentato da 500 a 800 caratteri per chunk con overlap di 100.
        """
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current = ""

        for paragraph in paragraphs:
            if len(paragraph) > chunk_size:
                sentences = paragraph.split(". ")
                for s in sentences:
                    if len(current) + len(s) + 2 <= chunk_size:
                        current += s + ". "
                    else:
                        if current:
                            chunks.append(current.strip())
                        # Overlap: mantieni l'ultima parte
                        if len(s) > overlap:
                            current = s[-overlap:] + ". "
                        else:
                            current = s + ". "
            else:
                if len(current) + len(paragraph) + 2 <= chunk_size:
                    current += paragraph + "\n\n"
                else:
                    if current:
                        chunks.append(current.strip())
                    # Overlap
                    if len(paragraph) > overlap:
                        current = paragraph[-overlap:] + "\n\n"
                    else:
                        current = paragraph + "\n\n"

        if current:
            chunks.append(current.strip())

        return chunks

    # ------------------ Indexing ------------------

    def index_document(self, collection: chromadb.Collection, document_id: int,
                       document_name: str, content: str) -> None:
        """
        Indicizza un documento nella collection (chunking + add).
        """
        chunks = self.chunk_text(content)

        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "document_id": document_id,
                "document_name": document_name,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })
            ids.append(f"doc_{document_id}_chunk_{i}")

        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def remove_document(self, collection: chromadb.Collection, document_id: int) -> None:
        """
        Rimuove tutti i chunk di un documento dalla collection.
        """
        results = collection.get(where={"document_id": document_id})
        if results and results.get("ids"):
            collection.delete(ids=results["ids"])

    # ------------------ Query ------------------

    def search_relevant_chunks(self, collection: chromadb.Collection,
                               query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Cerca i chunk più rilevanti per la query.
        Aumentato da 5 a 10 risultati per avere più contesto.
        """
        results = collection.query(query_texts=[query], n_results=n_results)

        formatted: List[Dict[str, Any]] = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results.get("metadatas", [])[0] if results.get("metadatas") else []
            dists = results.get("distances", [])[0] if results.get("distances") else []
            for i, doc in enumerate(docs):
                formatted.append({
                    "content": doc,
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": dists[i] if i < len(dists) else None,
                })

        return formatted

    # ------------------ Drop collection ------------------

    def delete_collection(self, subject_id: int, subject_name: str) -> None:
        """Elimina la collection della materia (se esiste)."""
        client = self._get_client()
        try:
            client.delete_collection(name=self._collection_name(subject_id, subject_name))
        except Exception:
            pass  # Collection non esiste o già rimossa
