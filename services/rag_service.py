# rag_service.py
"""
Servizio RAG (Retrieval-Augmented Generation) con Qdrant e embedding dinamici
(Ollama oppure Gemini) scelti via .env
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

import requests
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue


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

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embedding per una lista di testi"""
        if not texts:
            return []
        if isinstance(texts, str):
            texts = [texts]

        resp = requests.post(
            f"{self.base_url}/embeddings",
            headers=self._headers,
            json={"model": self.model_name, "input": texts},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = [item.get("embedding") for item in data.get("data", [])]
        
        out = []
        for emb in embeddings:
            if emb is None:
                continue
            try:
                out.append([float(x) for x in emb])
            except Exception:
                vals = emb.get("values") if isinstance(emb, dict) else None
                out.append([float(x) for x in (vals or [])])
        return out


class GeminiEmbeddingFunction:
    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        self.client = genai.Client(api_key=api_key)
        if not model.startswith("models/"):
            self.model_name = f"models/{model}"
        else:
            self.model_name = model

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embedding per una lista di testi"""
        if not texts:
            return []
        
        if isinstance(texts, str):
            texts = [texts]

        print(f"[DEBUG] Embedding {len(texts)} testi con Gemini...")
        
        # Filtra stringhe vuote
        valid_texts_map = {}
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts_map[i] = text
        
        batchable_texts = list(valid_texts_map.values())
        
        if not batchable_texts:
            print("[DEBUG] Nessun testo valido. Ritorno vettori di zeri.")
            return [[0.0] * 768] * len(texts)

        MAX_BATCH_SIZE = 100
        valid_embeddings_map = {}
        
        try:
            for i in range(0, len(batchable_texts), MAX_BATCH_SIZE):
                batch_texts = batchable_texts[i:i + MAX_BATCH_SIZE]
                
                print(f"[DEBUG] Batch {i//MAX_BATCH_SIZE + 1}/{(len(batchable_texts)-1)//MAX_BATCH_SIZE + 1}")
                
                try:
                    res = self.client.models.embed_content(
                        model=self.model_name,
                        contents=batch_texts,
                    )
                except Exception:
                    # Fallback: una chiamata per testo
                    batch_embeddings = []
                    for t in batch_texts:
                        single = self.client.models.embed_content(
                            model=self.model_name,
                            content=t,
                        )
                        emb_obj = getattr(single, "embedding", None)
                        values = getattr(emb_obj, "values", None) if emb_obj is not None else None
                        if values is None and isinstance(single, dict):
                            values = single.get("embedding", {}).get("values")
                        batch_embeddings.append([float(x) for x in (values or [])])
                    
                    for j, emb in enumerate(batch_embeddings):
                        valid_embeddings_map[i + j] = emb
                    continue
                
                # Normalizza il risultato
                embeddings_attr = getattr(res, "embeddings", None)
                if embeddings_attr is None:
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
                    valid_embeddings_map[i + j] = emb

        except Exception as e:
            print(f"ERRORE API: {e}")
            import traceback
            traceback.print_exc()
        
        # Ricostruisci lista finale
        embedding_dim = 768
        for emb in valid_embeddings_map.values():
            if emb is not None:
                embedding_dim = len(emb)
                break

        zero_vector = [0.0] * embedding_dim
        final_embeddings = []
        
        reconstructed_map = {}
        valid_indices_list = list(valid_texts_map.keys())
        
        for i, emb in valid_embeddings_map.items():
            original_index = valid_indices_list[i]
            reconstructed_map[original_index] = emb

        for i in range(len(texts)):
            emb = reconstructed_map.get(i)
            if emb is not None:
                final_embeddings.append(emb)
            else:
                final_embeddings.append(zero_vector)

        print(f"[DEBUG] Embedding completato. {len(final_embeddings)} vettori.")
        return final_embeddings


# ==========================
#        RAG SERVICE
# ==========================


class RAGService:
    """Servizio per implementare RAG con Qdrant.
    
    Implementa il pattern Singleton per evitare accessi concorrenti al database Qdrant.
    """
    
    _instance = None
    _lock = None
    
    def __new__(cls, persist_directory: str = "./qdrant_db"):
        """Singleton pattern: ritorna sempre la stessa istanza"""
        if cls._instance is None:
            print("[RAG] Creazione nuova istanza singleton di RAGService")
            cls._instance = super(RAGService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, persist_directory: str = "./qdrant_db"):
        """
        Args:
            persist_directory: Directory dove salvare il database Qdrant
        """
        # Evita reinizializzazione se l'istanza è già stata inizializzata
        if self._initialized:
            return
            
        print(f"[RAG] Inizializzazione RAGService con persist_directory: {persist_directory}")
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Client Qdrant in modalità embedded (salva su disco)
        self.client = QdrantClient(path=persist_directory)
        self._initialized = True
        
        # Configurazione embedding
        self.use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
        
        # Configurazione chunking da .env
        self.chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "800"))
        self.chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
        self.chunks_per_topic = int(os.getenv("RAG_CHUNKS_PER_TOPIC", "15"))
        # Soglia di similarità minima per considerare un risultato rilevante
        # Valori tipici 0.2-0.4 con COSINE; più alto = più stringente
        try:
            self.score_threshold = float(os.getenv("RAG_SCORE_THRESHOLD", "0.25"))
        except Exception:
            self.score_threshold = 0.25

        print(f"[RAG CONFIG] Chunk size: {self.chunk_size}, Overlap: {self.chunk_overlap}, Chunks per topic: {self.chunks_per_topic}")
        print(f"[RAG CONFIG] Score threshold: {self.score_threshold}")
            
        if self.use_local_llm:
            self.local_base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
            self.local_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
        else:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not self.gemini_api_key:
                print("ATTENZIONE: GEMINI_API_KEY non trovata.")
            self.gemini_embed_model = "text-embedding-004"
        
        self.embedder = self._create_embedding_function()
        
        # Determina la dimensione degli embedding
        self._embedding_dim = None

    def _create_embedding_function(self):
        """Crea l'embedder in base alle variabili d'ambiente."""
        if self.use_local_llm:
            print(f"[RAG] Provider: Ollama ({self.local_model})")
            return OllamaEmbeddingFunction(base_url=self.local_base_url, model=self.local_model)
        else:
            if not self.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY non impostata e USE_LOCAL_LLM=false")
            print(f"[RAG] Provider: Gemini ({self.gemini_embed_model})")
            return GeminiEmbeddingFunction(api_key=self.gemini_api_key, model=self.gemini_embed_model)

    def _get_embedding_dim(self) -> int:
        """Determina la dimensione degli embedding"""
        if self._embedding_dim is None:
            test_emb = self.embedder.embed(["test"])
            self._embedding_dim = len(test_emb[0]) if test_emb else 768
        return self._embedding_dim

    def _collection_name(self, subject_id: int, subject_name: str) -> str:
        """Nome standardizzato per la collection"""
        return f"subject_{subject_id}_{subject_name.lower().replace(' ', '_').replace('-', '_')}"

    def create_collection(self, subject_id: int, subject_name: str) -> str:
        """Crea/ottiene la collection per una materia"""
        collection_name = self._collection_name(subject_id, subject_name)
        
        # Verifica se la collection esiste già
        collections = self.client.get_collections().collections
        collection_exists = any(col.name == collection_name for col in collections)
        
        if not collection_exists:
            print(f"[RAG] Creazione nuova collection: {collection_name}")
            # Crea collection con la dimensione corretta
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self._get_embedding_dim(),
                    distance=Distance.COSINE
                )
            )
        else:
            print(f"[RAG] Collection esistente: {collection_name}")
        
        return collection_name

    # ------------------ Chunking ------------------
    # Sostituisci la tua vecchia funzione 'chunk_text' con questa

    def chunk_text_recursive_test(self, text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
        """
        Divide il testo in chunk usando una strategia ricorsiva.
        
        Args:
            text: Il testo da dividere.
            chunk_size: La dimensione massima desiderata per chunk (usa il default del servizio se None).
            chunk_overlap: La sovrapposizione desiderata (usa il default del servizio se None).
        
        Returns:
            Una lista di chunk di testo.
        """
        
        # Usa i valori di default configurati nel servizio se non forniti
        final_chunk_size = chunk_size if chunk_size is not None else self.chunk_size
        final_overlap = chunk_overlap if chunk_overlap is not None else self.chunk_overlap

        # Gerarchia dei separatori: dal più grande (logico) al più piccolo (brutale)
        separators = ["\n\n", "\n", ". ", " ", ""]
        
        # Inizia con il testo intero
        final_chunks = []
        
        # Funzione helper ricorsiva
        def _recursive_split(text: str, current_separators: List[str]):
            # Se il testo è già abbastanza piccolo, è un chunk
            if len(text) <= final_chunk_size:
                if text.strip(): # Assicurati che non sia solo spazio bianco
                    final_chunks.append(text.strip())
                return

            # Se abbiamo finito i separatori, dividiamo brutalmente
            if not current_separators:
                for i in range(0, len(text), final_chunk_size - final_overlap):
                    chunk = text[i : i + final_chunk_size]
                    if chunk.strip():
                        final_chunks.append(chunk.strip())
                return

            # Prendi il separatore corrente (il migliore)
            separator = current_separators[0]
            remaining_separators = current_separators[1:]

            # Cerca di dividere il testo con questo separatore
            # Usiamo un trucco per mantenere il separatore (utile per \n\n)
            if separator == "":
                splits = list(text) # Dividi per carattere
            else:
                splits = text.split(separator)

            current_chunk = ""
            for i, part in enumerate(splits):
                # Ricostruisci il testo con il separatore (tranne per l'ultimo pezzo)
                if i < len(splits) - 1:
                    part_with_separator = part + separator
                else:
                    part_with_separator = part
                
                # Se l'aggiunta di questa parte supera il limite...
                if len(current_chunk) + len(part_with_separator) > final_chunk_size:
                    
                    # Se il current_chunk non è vuoto, è un pezzo valido
                    if current_chunk:
                        # ...ma potrebbe essere ancora troppo grande, quindi RILANCIA la ricorsione
                        _recursive_split(current_chunk.strip(), remaining_separators)
                    
                    # Inizia un nuovo chunk, applicando l'overlap
                    # Prendi l'ultima parte del chunk precedente come overlap
                    overlap_text = current_chunk[-final_overlap:]
                    
                    # Se la parte stessa è più grande del chunk_size, lanciala da sola
                    if len(part_with_separator) > final_chunk_size:
                         _recursive_split(part_with_separator.strip(), remaining_separators)
                         current_chunk = "" # Resetta
                    else:
                        current_chunk = overlap_text + part_with_separator
                
                else:
                    current_chunk += part_with_separator
            
            # Non dimenticare l'ultimo chunk rimasto
            if current_chunk.strip():
                if len(current_chunk) > final_chunk_size:
                    _recursive_split(current_chunk.strip(), remaining_separators)
                else:
                    final_chunks.append(current_chunk.strip())

        # Avvia il processo
        _recursive_split(text, separators)
        
        # Filtra eventuali duplicati o chunk vuoti
        unique_chunks = list(dict.fromkeys(final_chunks))
        return [chunk for chunk in unique_chunks if chunk]

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Divide il testo in chunk con overlap"""
        # Usa i valori configurati se non specificati
        if chunk_size is None:
            chunk_size = self.chunk_size
        if overlap is None:
            overlap = self.chunk_overlap
            
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
                    if len(paragraph) > overlap:
                        current = paragraph[-overlap:] + "\n\n"
                    else:
                        current = paragraph + "\n\n"

        if current:
            chunks.append(current.strip())

        return chunks

    # ------------------ Indexing ------------------

    def index_document(self, collection_name: str, document_id: int,
                       document_name: str, content: str) -> None:
        """Indicizza un documento nella collection"""
        chunks = self.chunk_text(content)
        if not chunks:
            return

        print(f"[RAG] Indicizzazione documento {document_name}: {len(chunks)} chunks")
        
        # Genera embeddings
        embeddings = self.embedder.embed(chunks)
        
        if not embeddings:
            print("[RAG] Nessun embedding generato!")
            return
        
        # Prepara i punti per Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())  # ID univoco
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "document_name": document_name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "text": chunk
                    }
                )
            )
        
        # Inserisci in Qdrant
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        print(f"[RAG] Indicizzazione completata. {len(chunks)} chunks aggiunti.")

    def remove_document(self, collection_name: str, document_id: int) -> None:
        """Rimuove tutti i chunk di un documento dalla collection"""
        # Elimina tutti i punti con questo document_id
        self.client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        
        print(f"[RAG] Rimossi tutti i chunk del documento {document_id}")

    # ------------------ Query ------------------

    def is_document_indexed(self, collection_name: str, document_id: int) -> bool:
        """Ritorna True se esistono già punti in Qdrant per questo document_id."""
        try:
            count_res = self.client.count(
                collection_name=collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                exact=False,
            )
            total = getattr(count_res, "count", None)
            if total is None:
                # Alcune versioni possono restituire un int
                total = int(count_res) if count_res is not None else 0
            return (total or 0) > 0
        except Exception as e:
            print(f"[RAG] Errore in is_document_indexed: {e}")
            return False

    def get_all_chunks_texts(self, collection_name: str, batch_size: int = 1000) -> List[str]:
        """Recupera tutti i testi dei chunk salvati nella collection da Qdrant."""
        texts: List[str] = []
        next_offset = None
        try:
            while True:
                points, next_offset = self.client.scroll(
                    collection_name=collection_name,
                    limit=batch_size,
                    offset=next_offset,
                    with_payload=True,
                    with_vectors=False,
                )
                if not points:
                    break
                for p in points:
                    payload = getattr(p, "payload", None) or {}
                    t = payload.get("text")
                    if isinstance(t, str) and t.strip():
                        texts.append(t)
                if not next_offset:
                    break
        except Exception as e:
            print(f"[RAG] Errore in get_all_chunks_texts: {e}")
        return texts

    def search_relevant_chunks(self, collection_name: str,
                               query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Cerca i chunk più rilevanti per la query"""
        # Embedding della query
        query_embedding = self.embedder.embed([query])
        if not query_embedding:
            return []
        
        # Cerca con Qdrant
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding[0],
            limit=n_results,
            score_threshold=self.score_threshold,
            with_payload=True,
            with_vectors=False,
        )
        
        # Formatta i risultati
        formatted = []
        for result in results:
            formatted.append({
                "content": result.payload.get("text", ""),
                "metadata": {
                    "document_id": result.payload.get("document_id"),
                    "document_name": result.payload.get("document_name"),
                    "chunk_index": result.payload.get("chunk_index"),
                    "total_chunks": result.payload.get("total_chunks"),
                },
                "score": result.score,
                "distance": 1 - result.score,  # mantenuto per retrocompatibilità
            })
        
        return formatted

    # ------------------ Drop collection ------------------

    def delete_collection(self, subject_id: int, subject_name: str) -> None:
        """Elimina la collection della materia"""
        collection_name = self._collection_name(subject_id, subject_name)
        
        try:
            self.client.delete_collection(collection_name=collection_name)
            print(f"[RAG] Collection eliminata: {collection_name}")
        except Exception as e:
            print(f"[RAG] Errore eliminazione collection {collection_name}: {e}")
    
    # ------------------ Cleanup ------------------
    
    @classmethod
    def close(cls):
        """Chiude la connessione Qdrant e resetta il singleton.
        
        Utile per test o quando si vuole reinizializzare il servizio.
        NOTA: In produzione NON è necessario chiamare questo metodo,
        il singleton rimane attivo per tutta la vita dell'applicazione.
        """
        if cls._instance is not None and hasattr(cls._instance, 'client'):
            try:
                # Qdrant client non ha un metodo close() esplicito,
                # ma possiamo forzare la garbage collection
                cls._instance.client = None
                print("[RAG] Client Qdrant chiuso")
            except Exception as e:
                print(f"[RAG] Errore durante chiusura client: {e}")
            finally:
                cls._instance = None
                print("[RAG] Singleton RAGService resettato")
