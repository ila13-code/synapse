import os
import traceback

from PyQt6.QtCore import (QEasingCurve, QPropertyAnimation, Qt, QThread,
                          QTimer, pyqtSignal)
from PyQt6.QtGui import QColor, QFont, QTextOption
from PyQt6.QtWidgets import (QCheckBox, QFileDialog, QFrame,
                             QGraphicsOpacityEffect, QGridLayout, QHBoxLayout,
                             QLabel, QMainWindow, QMessageBox, QProgressDialog,
                             QPushButton, QScrollArea, QSpinBox, QTabWidget,
                             QTextEdit, QVBoxLayout, QWidget)

from config.env_loader import get_env_bool
from database.db_manager import DatabaseManager
from services.ai_local_service import LocalLLMService
from services.ai_service import AIService
from services.files.export_service import ExportService
from services.files.file_service import FileService
from services.tools.latex_service import LaTeXService
from services.rag_service import RAGService
from services.reflection_service import ReflectionService
from services.tools.web_search_service import WebSearchService
from ui.dialogs import EditFlashcardDialog, ToggleSwitch
from ui.icons import IconProvider
from ui.styles import (get_caption_text_color, get_card_background,
                       get_icon_color, get_secondary_text_color,
                       get_text_color, get_theme_colors, get_theme_style)
from ui.subject_styles import (get_caption_label_style,
                               get_delete_button_style,
                               get_document_card_style, get_documents_list_bg,
                               get_flashcard_textedit_style,
                               get_text_label_style, get_upload_card_style,
                               get_web_search_frame_style)


class DocumentUploadThread(QThread):
    """Thread per caricare e indicizzare documenti in background"""
    finished = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, file_path, subject_id, subject_name, file_service, db, rag_service):
        super().__init__()
        self.file_path = file_path
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.file_service = file_service
        self.db = db                  # lasciato per compatibilità, NON usato nel thread
        self.rag_service = rag_service
    
    def run(self):
        try:
            # 1) Salva il documento (OK farlo qui se FileService è thread-safe)
            doc_id = self.file_service.save_document(self.file_path, self.subject_id)
            if not doc_id:
                self.finished.emit(False, "Errore durante il caricamento del documento")
                return

            # 2) Usa un DatabaseManager NUOVO dentro il thread (fix per SQLite)
            try:
                from database.db_manager import DatabaseManager
                db = DatabaseManager()  # connessione legata a questo thread
            except Exception as e:
                self.finished.emit(False, f"Errore inizializzazione DB nel thread: {e}")
                return

                        # 3) Indicizzazione RAG (non bloccare l'upload se fallisce)
            try:
                doc = db.get_document(doc_id)
                if doc and doc.get('content'):
                    collection_name = self.rag_service.create_collection(self.subject_id, self.subject_name)
                    self.rag_service.index_document(
                        collection_name,
                        doc['id'],
                        doc['name'],
                        doc['content']
                    )
            except Exception as e:
                # Logga ma non fallire l'upload
                print(f"Errore indicizzazione RAG: {e}")

            # 4) Fine OK
            self.finished.emit(True, "Documento caricato e indicizzato con successo!")
        
        except Exception as e:
            self.finished.emit(False, f"Errore: {str(e)}")

class Snackbar(QFrame):
    """Widget snackbar che scompare automaticamente"""
    
    def __init__(self, message, parent=None, duration=3000):
        super().__init__(parent)
        self.duration = duration  # Durata in millisecondi
        self.setProperty("class", "snackbar")
        self.setFixedHeight(50)
        
        # Stile - SOLO LIGHT
        bg_color = "#424242"
        text_color = "#FFFFFF"
        
        self.setStyleSheet(f"""
            QFrame[class="snackbar"] {{
                background-color: {bg_color};
                border-radius: 8px;
                padding: 12px 24px;
            }}
            QLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        
        # Icona successo
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, "check", 20, "#10B981")
        layout.addWidget(icon_label)
        
        # Messaggio
        msg_label = QLabel(message)
        layout.addWidget(msg_label)
        layout.addStretch()
        
        # Effetto opacità per animazione
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
    def show_animated(self):
        """Mostra con animazione fade-in"""
        self.show()
        
        # Animazione fade-in
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_in_animation.start()
        
        # Timer per nascondere dopo il tempo specificato
        QTimer.singleShot(self.duration, self.hide_animated)
    
    def hide_animated(self):
        """Nascondi con animazione fade-out"""
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_animation.finished.connect(self.deleteLater)
        self.fade_out_animation.start()


class GenerationThread(QThread):
    """Thread per generare flashcard con RAG e Reflection"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str, str)  # (titolo, messaggio)
    progress = pyqtSignal(int, str)  # (percentuale, messaggio)
    
    def __init__(self, ai_service, rag_service, reflection_service, 
                 subject_id, subject_name, documents, num_cards=10, 
                 use_web_search=False, use_rag=True, use_reflection=True,
                 user_query=None, web_search_service=None):  # NUOVO PARAMETRO
        super().__init__()
        self.ai_service = ai_service
        self.rag_service = rag_service
        self.reflection_service = reflection_service
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.documents = documents
        self.num_cards = num_cards
        self.use_web_search = use_web_search
        self.use_rag = use_rag
        self.use_reflection = use_reflection
        self.user_query = user_query  # NUOVO ATTRIBUTO
        self.web_search_service = web_search_service  # Servizio ricerca web
    
    def run(self):
        try:
            print("[DEBUG] Avvio di GenerationThread.run()...")
            
            if self.use_rag:
                print("[DEBUG] Scelta modalità RAG.")
                flashcards = self._generate_with_rag()
            else:
                print("[DEBUG] Scelta modalità Tradizionale.")
                flashcards = self._generate_traditional()
            
            print("[DEBUG] Generazione completata con successo.")
            self.finished.emit(flashcards) # <-- EMETTI SEGNALE DI SUCCESSO

        except Exception as e:
            print("======================================================")
            print(f"ERRORE FATALE CATTURATO IN 'run': {e}")
            traceback.print_exc() # Stampa già il traceback
            print("======================================================")
            
            # EMETTI SEGNALE DI ERRORE per mostrarlo nella UI
            self.error.emit("Errore durante la generazione", str(e))
    
    def _generate_traditional(self):
        """Generazione tradizionale (Context Stuffing) - metodo attuale"""
        self.progress.emit(10, "Combinando documenti...")
        
        # Combina tutto il contenuto
        all_content = []
        for doc in self.documents:
            if doc['content']:
                all_content.append(doc['content'])
        
        combined_content = "\n\n".join(all_content)

        # Se la ricerca web è abilitata, arricchisci il contesto
        if self.use_web_search and self.web_search_service:
            search_query = self.user_query or self.subject_name
            self.progress.emit(55, f"Ricerca web: {search_query[:50]}...")
            print(f"[WEB] Avvio ricerca web (tradizionale) con query: '{search_query}'")
            try:
                web_block = self.web_search_service.enrich_context_block(search_query, max_results=4)
            except Exception:
                web_block = ""
            if web_block:
                combined_content += f"\n\n{web_block}\n"
                print("[WEB] Ricerca web completata (tradizionale) e integrata nel contesto")
            else:
                print("[WEB] Nessun risultato web (tradizionale) o errore durante la ricerca")
        
        self.progress.emit(50, "Generando flashcard...")
        
        # Genera con il metodo tradizionale
        flashcards = self.ai_service.generate_flashcards(
            combined_content, 
            self.num_cards,
            self.use_web_search
        )
        
        self.progress.emit(100, "Completato!")
        return flashcards
    
    def _generate_with_rag(self):
        try:
            print("[DEBUG] 1. Avvio _generate_with_rag.")
            flashcards = []
            
            # Step 1: Crea/Ottieni collection
            self.progress.emit(5, "Inizializzando vector database...")
            print("[DEBUG] 2. Creazione collection...")
            collection_name = self.rag_service.create_collection(
                self.subject_id, 
                self.subject_name
            )
            
            # Step 2: Indicizza SOLO i documenti non ancora presenti in Qdrant
            self.progress.emit(10, "Verifica indicizzazione documenti...")
            print("[DEBUG] 3. Verifica/indicizzazione RAG...")
            for i, doc in enumerate(self.documents):
                if not doc.get('content'):
                    continue
                try:
                    already = self.rag_service.is_document_indexed(collection_name, doc['id'])
                except Exception:
                    already = False
                if already:
                    progress_pct = 10 + (i + 1) * 5 // max(1, len(self.documents))
                    self.progress.emit(progress_pct, f"Già indicizzato: {doc['name']}")
                    continue
                # Indicizza documento non presente
                self.rag_service.index_document(
                    collection_name,
                    doc['id'],
                    doc['name'],
                    doc['content']
                )
                progress_pct = 10 + (i + 1) * 10 // max(1, len(self.documents))
                self.progress.emit(progress_pct, f"Indicizzato: {doc['name']}")
            print("[DEBUG] 3. Verifica/indicizzazione RAG completata.")

            
            # Step 3: Usa SEMPRE i chunk salvati in Qdrant per l'analisi dei topic
            print("[DEBUG] 4. Lettura chunks dalla collection...")
            self.progress.emit(25, "Recupero contenuti indicizzati...")
            all_chunks = self.rag_service.get_all_chunks_texts(collection_name)
            if not all_chunks:
                # Fallback (non dovrebbe succedere): ricava dai documenti in memoria
                print("[DEBUG] Nessun chunk trovato in Qdrant: fallback a chunking in memoria")
                for doc in self.documents:
                    if doc.get('content'):
                        all_chunks.extend(self.rag_service.chunk_text(doc['content']))
            
            # Step 4: Estrai topic principali
            print("[DEBUG] 5. Estrazione topics...")
            
            # Se l'utente ha fornito una query, usala per focalizzare i topic
            if self.user_query and self.user_query.strip():
                user_q = self.user_query.strip()
                self.progress.emit(30, f"Ricerca contenuti per: {user_q}")
                print(f"[DEBUG] Usando query utente: {user_q}")

                # IMPORTANTE: Se l'utente fa una domanda specifica, 
                # i topic devono essere estratti DALLA DOMANDA, non dai documenti!
                # I documenti servono solo come contesto per rispondere.
                
                print(f"[DEBUG] Estrazione topic DALLA QUERY utente (non dai documenti)")
                topics = self.reflection_service.extract_topics([user_q], self.num_cards)
                if not topics:
                    topics = [user_q]
                self.progress.emit(35, f"Identificati {len(topics)} argomenti dalla query utente")
            else:
                # Altrimenti estrai automaticamente i topic
                topics = self.reflection_service.extract_topics(all_chunks, self.num_cards)
                self.progress.emit(35, f"Identificati {len(topics)} argomenti")

            # Limita i topic al numero richiesto
            topics = topics[:self.num_cards]
            
            # Step 5: Per ogni topic, genera flashcard con RAG + Reflection
            print("[DEBUG] 6. Inizio generazione per topic...")
            for i, topic in enumerate(topics):
                try:
                    base_progress = 35 + (i * 65 // len(topics))
                    
                    self.progress.emit(base_progress, f"Analizzando: {topic}")
                    
                    # IMPORTANTE: Se c'è una query utente, combina topic + query per la ricerca
                    # Questo evita di trovare chunks irrilevanti che matchano solo parole generiche
                    if self.user_query and self.user_query.strip():
                        # Cerca usando "topic NEL CONTESTO DELLA query utente"
                        search_query = f"{topic} (nel contesto di: {self.user_query.strip()})"
                        print(f"[RAG-DEBUG] Cerco chunks per topic '{topic}' nel contesto della query utente")
                    else:
                        search_query = topic
                        print(f"[RAG-DEBUG] Cerco chunks per topic: '{topic}'")
                    
                    relevant_chunks = self.rag_service.search_relevant_chunks(
                        collection_name, 
                        search_query, 
                        n_results=self.rag_service.chunks_per_topic  # Usa configurazione
                    )
                    
                    # Log dei chunks recuperati
                    print(f"[RAG-DEBUG] Trovati {len(relevant_chunks)} chunks rilevanti per '{topic}'")
                    if relevant_chunks:
                        for idx, chunk in enumerate(relevant_chunks[:3]):  # Mostra solo i primi 3
                            print(f"  Chunk {idx+1}: {chunk['content'][:100]}... (da '{chunk['metadata']['document_name']}')")
                    
                    context = "\n\n".join([chunk['content'] for chunk in relevant_chunks])

                    # Integra snippet web per la domanda utente (NON per il topic!) se richiesto
                    if self.use_web_search and self.web_search_service:
                        # Usa la query originale dell'utente, non il topic estratto dal RAG
                        web_query = self.user_query or topic
                        print(f"[WEB] Avvio ricerca web per query utente: '{web_query}' (topic RAG era: '{topic}')")
                        try:
                            web_block = self.web_search_service.enrich_context_block(web_query, max_results=3)
                        except Exception:
                            web_block = ""
                        if web_block:
                            context += f"\n\n{web_block}\n"
                            print(f"[WEB] Ricerca web completata per query '{web_query}' e integrata nel contesto")
                        else:
                            print(f"[WEB] Nessun risultato web per query '{web_query}' o errore durante la ricerca")
                    
                    if self.use_reflection:
                        self.progress.emit(
                            base_progress + 5, 
                            f"Generando con Reflection: {topic}"
                        )
                        flashcard = self.reflection_service.generate_flashcard_with_reflection(
                            context, 
                            topic,
                            max_iterations=2
                        )
                    else:
                        flashcard = self.reflection_service.generate_flashcard_draft(
                            context, 
                            topic
                        )
                    
                    flashcards.append(flashcard)

                    # Interrompi se abbiamo raggiunto il numero richiesto
                    if len(flashcards) >= self.num_cards:
                        break
                    
                except Exception as e_topic:
                    # Non bloccare tutto se un solo topic fallisce
                    print(f"Errore generando flashcard per '{topic}': {e_topic}")
                    continue
            
            print("[DEBUG] 7. Generazione _generate_with_rag completata.")
            self.progress.emit(100, "Generazione completata!")
            return flashcards

        except ConnectionError as e:
            print("======================================================")
            print(f"ERRORE CONNESSIONE in '_generate_with_rag': {e}")
            print("======================================================")
            # Messaggio utente più chiaro
            self.error.emit(
                "Servizio di embedding non disponibile",
                str(e)
            )
            return []
        except Exception as e:
            print("======================================================")
            print(f"ERRORE CRITICO in '_generate_with_rag': {e}")
            traceback.print_exc()
            print("======================================================")
            # Rilancia l'eccezione per farla catturare dal 'run'
            raise e


class SubjectWindow(QMainWindow):
    def __init__(self, subject_data, parent=None):  
        super().__init__(parent)
        self.subject_data = subject_data
        self.db = DatabaseManager()
        self.file_service = FileService()
        self.rag_service = RAGService()  # Inizializza RAG service
        self.web_search_service = WebSearchService()  # Servizio ricerca web
        self.current_flashcard_index = 0
        self.is_flipped = False
        self.flashcards = []
        # Mantieni i thread di upload per evitare che vengano garbage-collected
        self.upload_threads = []
        self.setup_ui()
        self.load_data()
        self.load_test_query()  # Carica automaticamente la query di test
    
    def load_test_query(self):
        """Carica automaticamente la query dal file user_question.txt se esiste"""
        test_file = os.path.join(os.path.dirname(__file__), '..', 'user_question.txt')
        if os.path.exists(test_file):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    user_query = f.read().strip()
                if user_query and hasattr(self, 'user_query_input'):
                    self.user_query_input.setPlainText(user_query)
                    print(f"[TEST MODE] Caricata query da user_question.txt: {user_query}")
            except Exception as e:
                print(f"[TEST MODE] Errore lettura user_question.txt: {e}")
    
    def get_color_with_opacity(self, hex_color, opacity=0.2):
        """Converte un colore hex in rgba con opacità specificata"""
        color = QColor(hex_color)
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {opacity})"
        
    def setup_ui(self):
        self.setWindowTitle(f"Synapse - {self.subject_data['name']}")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(get_theme_style())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        documents_icon = IconProvider.get_icon("document", 18, get_icon_color())
        generate_icon = IconProvider.get_icon("sparkles", 18, get_icon_color())
        flashcards_icon = IconProvider.get_icon("cards", 18, get_icon_color())
        
        self.documents_tab = self.create_documents_tab()
        self.tabs.addTab(self.documents_tab, documents_icon, "Documenti")
        
        self.generate_tab = self.create_generate_tab()
        self.tabs.addTab(self.generate_tab, generate_icon, "Genera")
        
        self.flashcards_tab = self.create_flashcards_tab()
        self.tabs.addTab(self.flashcards_tab, flashcards_icon, "Flashcard")
        
        main_layout.addWidget(self.tabs)
    
    def create_documents_tab(self):
        """Tab per gestire i documenti della materia"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        upload_card = self.create_upload_card()
        layout.addWidget(upload_card)
        
        self.docs_header = QLabel("Documenti Caricati (0)")
        self.docs_header.setStyleSheet(get_text_label_style(18, 700))
        layout.addWidget(self.docs_header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        theme = self.db.get_setting('theme', 'light')
        list_bg = get_documents_list_bg(theme)
        scroll_content.setStyleSheet(f"background-color: {list_bg};")
        self.docs_layout = QVBoxLayout(scroll_content)
        self.docs_layout.setSpacing(12)
        self.docs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_upload_card(self):
        """Crea la card per l'upload dei documenti"""
        card = QFrame()
        theme = self.db.get_setting('theme', 'light')
        card.setStyleSheet(get_upload_card_style(theme))
        card.setFixedHeight(220)  # Aumentato da 180 a 220
        
        # Abilita drag & drop sul widget della card con handler sicuri
        card.setAcceptDrops(True)

        def card_dragEnterEvent(event):
            try:
                md = event.mimeData()
                # Accetta solo se contiene URL locali con estensione supportata
                if md and md.hasUrls():
                    urls = [u for u in md.urls() if u.isLocalFile()]
                    for u in urls:
                        path = u.toLocalFile()
                        if path and os.path.isfile(path) and path.lower().endswith((".pdf", ".txt")):
                            event.acceptProposedAction()
                            return
                event.ignore()
            except Exception:
                # In caso di qualunque errore, non far crashare l'app
                event.ignore()

        def card_dropEvent( event):
            try:
                md = event.mimeData()
                if not (md and md.hasUrls()):
                    event.ignore()
                    return

                urls = md.urls() or []
                files = []
                for u in urls:
                    try:
                        if not u.isLocalFile():
                            continue
                        path = u.toLocalFile()
                        if not path:
                            continue
                        if not os.path.isfile(path):
                            continue
                        if path.lower().endswith((".pdf", ".txt")):
                            files.append(path)
                    except Exception:
                        continue

                if not files:
                    QMessageBox.warning(
                        self,
                        "File non validi",
                        "Sono supportati solo file PDF e TXT"
                    )
                    event.ignore()
                    return

                event.acceptProposedAction()
                for fp in files:
                    self._process_uploaded_file(fp)
            except Exception as e:
                # Mostra un messaggio invece di crashare
                QMessageBox.critical(self, "Errore", f"Errore durante il drop dei file: {e}")
                event.ignore()

        # Collega gli handler locali alla card
        card.dragEnterEvent = card_dragEnterEvent
        card.dropEvent = card_dropEvent
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, "upload", 48, "#8B5CF6")
        layout.addWidget(icon_label)
        
        title_label = QLabel("Carica Documenti")
        title_label.setStyleSheet(get_text_label_style(18, 600))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel("Carica file PDF o TXT per creare flashcard\n(oppure trascina i file qui)")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(get_caption_label_style(13))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        upload_btn = QPushButton("Seleziona File")
        upload_btn.setProperty("class", "primary")
        upload_btn.clicked.connect(self.upload_document)
        layout.addWidget(upload_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return card
    
    def create_document_card(self, doc):
        """Crea una card per visualizzare un documento"""
        card = QFrame()
        theme = self.db.get_setting('theme', 'light')
        card.setStyleSheet(get_document_card_style(theme))
        card.setFixedHeight(80)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, "file_text", 32, "#8B5CF6")
        layout.addWidget(icon_label)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(doc['name'])
        name_label.setStyleSheet(get_text_label_style(14, 600))
        info_layout.addWidget(name_label)
        
        size_text = self.file_service.format_file_size(doc['size_bytes'] or 0)
        date_text = doc['created_at'][:10]
        meta_label = QLabel(f"{size_text} • {date_text}")
        meta_label.setStyleSheet(get_caption_label_style(12))
        info_layout.addWidget(meta_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        delete_btn = QPushButton()
        delete_btn.setIcon(IconProvider.get_icon("trash", 18, "#EF4444"))
        delete_btn.setProperty("class", "icon-button")
        delete_btn.setFixedSize(36, 36)
        delete_btn.clicked.connect(lambda: self.delete_document(doc['id']))
        delete_btn.setStyleSheet(get_delete_button_style())
        layout.addWidget(delete_btn)
        
        return card
    
    def create_generate_tab(self):
        """Tab per generare flashcard con AI"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        gen_card = QFrame()
        gen_card.setProperty("class", "card")
        gen_card.setFixedWidth(900)
        
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setContentsMargins(30, 30, 30, 30)
        gen_layout.setSpacing(20)
        
        # Rimosso: icon_label con bacchetta magica
        # Rimosso: title_label "Genera Flashcard con AI"
        
        desc_label = QLabel(
            "Analizza i tuoi documenti e genera flashcard personalizzate "
            "utilizzando l'intelligenza artificiale"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(get_text_label_style(16, 500))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setContentsMargins(0, 0, 0, 10)
        gen_layout.addWidget(desc_label)
        
        primary_color = '#8B5CF6'
        doc_bg = get_card_background()
        
        self.doc_count_label = QLabel("Documenti disponibili: 0")
        self.doc_count_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {primary_color};
            background-color: {doc_bg}; 
            padding: 16px;
            border: 1px solid {primary_color}50;
            border-radius: 12px;
        """)
        self.doc_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_layout.addWidget(self.doc_count_label)
        
        web_search_frame = self.create_web_search_option()
        gen_layout.addWidget(web_search_frame)
        
        # === Numero di flashcard da generare ===
        count_label = QLabel("Numero di Flashcard")
        count_label.setStyleSheet(get_text_label_style(14, 600))
        gen_layout.addWidget(count_label)

        count_layout = QHBoxLayout()
        count_layout.setSpacing(12)

        self.num_cards_spin = QSpinBox()
        self.num_cards_spin.setRange(1, 100)
        try:
            default_num = int(self.db.get_setting('flashcards_per_generation', '10'))
        except Exception:
            default_num = 10
        self.num_cards_spin.setValue(max(1, min(100, default_num)))
        self.num_cards_spin.setToolTip("Numero massimo di flashcard da generare")
        self.num_cards_spin.setMinimumHeight(44)
        self.num_cards_spin.setMinimumWidth(120)
        
        # Stile migliorato per il QSpinBox - bordi sottili e colori coerenti
        self.num_cards_spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.num_cards_spin.setStyleSheet(f"""
            QSpinBox {{
                font-size: 16px;
                font-weight: 600;
                padding: 8px 12px;
                border: 1px solid {primary_color}60;
                border-radius: 8px;
                background-color: {doc_bg};
                color: {get_text_color()};
            }}
            QSpinBox:focus {{
                border: 1px solid {primary_color};
            }}
            QSpinBox::up-button {{
                width: 32px;
                border-radius: 4px;
                background-color: {primary_color};
                subcontrol-origin: border;
                subcontrol-position: top right;
            }}
            QSpinBox::down-button {{
                width: 32px;
                border-radius: 4px;
                background-color: {primary_color};
                subcontrol-origin: border;
                subcontrol-position: bottom right;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {primary_color}DD;
            }}
        """)
        
        # Persisti la scelta dell'utente
        self.num_cards_spin.valueChanged.connect(
            lambda v: self.db.set_setting('flashcards_per_generation', str(v))
        )
        count_layout.addWidget(self.num_cards_spin)
        count_layout.addStretch()
        gen_layout.addLayout(count_layout)

        # === NUOVA SEZIONE: Query utente per RAG ===
        query_label = QLabel("Query Personalizzata (opzionale)")
        query_label.setStyleSheet(get_text_label_style(14, 600))
        gen_layout.addWidget(query_label)
        
        self.user_query_input = QTextEdit()
        self.user_query_input.setPlaceholderText(
            "Inserisci una domanda o argomento specifico per guidare la generazione delle flashcard...\n"
            "Esempio: 'Quali sono le differenze tra NoSQL e database relazionali?'"
        )
        self.user_query_input.setFixedHeight(80)
        self.user_query_input.setStyleSheet(f"""
            QTextEdit {{
                font-size: 14px;
                padding: 12px;
                border: 2px solid {primary_color}40;
                border-radius: 8px;
                background-color: {doc_bg};
                color: {get_text_color()};
            }}
            QTextEdit:focus {{
                border: 2px solid {primary_color};
            }}
        """)
        gen_layout.addWidget(self.user_query_input)
        # === FINE NUOVA SEZIONE ===
        
        generate_btn = QPushButton(" Genera Flashcard")
        generate_btn.setIcon(IconProvider.get_icon("sparkles", 18, "#FFFFFF"))
        generate_btn.setProperty("class", "primary")
        generate_btn.setFixedHeight(50)
        generate_btn.clicked.connect(self.generate_flashcards)
        gen_layout.addWidget(generate_btn)
        
        layout.addWidget(gen_card)
        
        return widget
    
    def create_web_search_option(self):
        """Crea il frame per l'opzione di ricerca web"""
        frame = QFrame()
        frame.setStyleSheet(get_web_search_frame_style())
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        web_icon = QLabel()
        IconProvider.setup_icon_label(web_icon, "globe", 24, "#3B82F6")
        layout.addWidget(web_icon)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Ricerca Web")
        title.setStyleSheet(get_text_label_style(14, 600))
        text_layout.addWidget(title)
        
        # Verifica se TAVILY_API_KEY è presente
        has_tavily_key = bool(os.environ.get('TAVILY_API_KEY', '').strip())
        
        desc_text = "Integra informazioni aggiornate dal web"
        if not has_tavily_key:
            desc_text = "Richiede TAVILY_API_KEY (configura nelle impostazioni)"
        
        desc = QLabel(desc_text)
        desc.setStyleSheet(get_caption_label_style(12))
        text_layout.addWidget(desc)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        self.web_search_checkbox = ToggleSwitch()
        # Disabilita il toggle se non c'è la chiave
        if not has_tavily_key:
            self.web_search_checkbox.setEnabled(False)
            self.web_search_checkbox.setToolTip("Configura TAVILY_API_KEY nelle impostazioni per abilitare")
        layout.addWidget(self.web_search_checkbox)
        
        return frame
    
    def create_flashcards_tab(self):
        """Tab per visualizzare e gestire le flashcard"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        header_layout = QHBoxLayout()
        
        self.flashcard_counter = QLabel("0 / 0")
        self.flashcard_counter.setStyleSheet(get_text_label_style(18, 700))
        header_layout.addWidget(self.flashcard_counter)
        header_layout.addStretch()
        
        export_btn = QPushButton(" Esporta")
        export_btn.setIcon(IconProvider.get_icon("download", 18, get_icon_color()))
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(self.export_flashcards)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        self.flashcard_card = self.create_flashcard_display()
        layout.addWidget(self.flashcard_card, alignment=Qt.AlignmentFlag.AlignCenter)
        
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        
        edit_btn = QPushButton(" Modifica")
        edit_btn.setIcon(IconProvider.get_icon("edit", 18, get_icon_color()))
        edit_btn.setProperty("class", "secondary")
        edit_btn.clicked.connect(self.edit_current_flashcard)
        action_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton(" Elimina")
        delete_btn.setIcon(IconProvider.get_icon("trash", 18, "#EF4444"))
        delete_btn.setProperty("class", "secondary")
        delete_btn.clicked.connect(self.delete_current_flashcard)
        action_layout.addWidget(delete_btn)
        
        layout.addLayout(action_layout)
        
        nav_layout = self.create_navigation_controls()
        layout.addLayout(nav_layout)
        
        return widget
    


    def create_flashcard_display(self):
        """Crea la card per visualizzare la flashcard corrente"""
        card = QFrame()
        card.setProperty("class", "flashcard")
        card.setFixedWidth(900) 
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        card.mousePressEvent = lambda e: self.flip_card()
        
        self.flashcard_layout = QVBoxLayout(card)
        self.flashcard_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flashcard_layout.setSpacing(20)
        
        self.flashcard_label = QTextEdit("Nessuna flashcard disponibile")
        self.flashcard_label.setReadOnly(True) 
        self.flashcard_label.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere) 
        self.flashcard_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.flashcard_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.flashcard_label.setStyleSheet(get_flashcard_textedit_style())
        self.flashcard_label.setMinimumHeight(200)

        self.flashcard_layout.addWidget(self.flashcard_label)
        
        self.difficulty_label = QLabel()
        self.difficulty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.difficulty_label.hide()
        self.flashcard_layout.addWidget(self.difficulty_label)
        
        self.hint_label = QLabel("Clicca per girare la carta")
        self.hint_label.setStyleSheet(get_caption_label_style(14) + " margin-top: 20px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flashcard_layout.addWidget(self.hint_label)
        
        return card


    def create_navigation_controls(self):
        """Crea i controlli di navigazione per le flashcard"""
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(12)
        
        self.prev_btn = QPushButton(" Precedente")
        self.prev_btn.setIcon(IconProvider.get_icon("arrow-left", 16, get_icon_color()))
        self.prev_btn.setProperty("class", "secondary")
        self.prev_btn.setFixedWidth(150)
        self.prev_btn.clicked.connect(self.previous_flashcard)
        nav_layout.addWidget(self.prev_btn)
        
        flip_btn = QPushButton("Gira Carta")
        flip_btn.setProperty("class", "secondary")
        flip_btn.setFixedWidth(150)
        flip_btn.clicked.connect(self.flip_card)
        nav_layout.addWidget(flip_btn)
        
        self.next_btn = QPushButton("Successivo ▶")
        self.next_btn.setProperty("class", "secondary")
        self.next_btn.setFixedWidth(150)
        self.next_btn.clicked.connect(self.next_flashcard)
        nav_layout.addWidget(self.next_btn)
        
        return nav_layout
    
    # ==================== GESTIONE DATI ====================
    
    def load_data(self):
        """Carica tutti i dati necessari"""
        self.load_documents()
        self.load_flashcards()
        self.update_doc_count()
    
    def load_documents(self):
        """Carica e visualizza i documenti"""
        while self.docs_layout.count():
            child = self.docs_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        documents = self.db.get_documents_by_subject(self.subject_data['id'])
        
        self.docs_header.setText(f"Documenti Caricati ({len(documents)})")
        
        if not documents:
            empty_label = QLabel("Nessun documento caricato ancora")
            empty_label.setStyleSheet(get_caption_label_style(14) + " padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.docs_layout.addWidget(empty_label)
            return
        
        for doc in documents:
            doc_card = self.create_document_card(doc)
            self.docs_layout.addWidget(doc_card)
    
    def upload_document(self):
        """Gestisce l'upload di un nuovo documento"""
        options = QFileDialog.Options()
        # Usa il dialog Qt (non nativo) in modo che rispetti gli stylesheet dell'app
        options |= QFileDialog.Option.DontUseNativeDialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleziona Documenti",
            "",
            "Documenti (*.txt *.pdf)",
            options=options
        )

        if not file_paths:
            return

        for file_path in file_paths:
            if file_path and os.path.isfile(file_path):
                self._process_uploaded_file(file_path)
    
    # I metodi globali di drag/drop non sono più collegati direttamente al widget,
    # ma lasciamoli come fallback generici (non usati dalla card)
    def dragEnterEvent(self, event):
        try:
            if event.mimeData() and event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()
        except Exception:
            event.ignore()

    def dropEvent(self, event):
        try:
            md = event.mimeData()
            if not (md and md.hasUrls()):
                event.ignore()
                return
            files = []
            for u in md.urls() or []:
                if u.isLocalFile():
                    p = u.toLocalFile()
                    if p and os.path.isfile(p) and p.lower().endswith((".pdf", ".txt")):
                        files.append(p)
            if not files:
                QMessageBox.warning(self, "File non validi", "Sono supportati solo file PDF e TXT")
                event.ignore()
                return
            event.acceptProposedAction()
            for fp in files:
                self._process_uploaded_file(fp)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il drop dei file: {e}")
            event.ignore()
    
    def _process_uploaded_file(self, file_path):
        """Processa un singolo file caricato in background con feedback visivo"""
        # Mostra dialog di loading
        loading = QProgressDialog("Caricamento in corso...", None, 0, 0, self)
        loading.setWindowTitle("Caricamento Documento")
        loading.setWindowModality(Qt.WindowModality.WindowModal)
        loading.setCancelButton(None)  # Non cancellabile
        loading.setMinimumDuration(0)
        loading.setValue(0)
        loading.show()
        
        # Crea e avvia thread
        upload_thread = DocumentUploadThread(
            file_path,
            self.subject_data['id'],
            self.subject_data['name'],
            self.file_service,
            self.db,
            self.rag_service
        )
        
        # Connetti i segnali
        def on_finished(success, msg):
            try:
                self._on_upload_finished(success, msg, loading)
            finally:
                # Rimuovi il thread dalla lista quando termina
                try:
                    self.upload_threads.remove(upload_thread)
                except ValueError:
                    pass

        upload_thread.finished.connect(on_finished)

        # Conserva un riferimento per evitare GC anticipata quando carichiamo più file
        self.upload_threads.append(upload_thread)
        upload_thread.start()
    
    def _on_upload_finished(self, success, message, loading_dialog):
        """Callback quando l'upload è completato"""
        loading_dialog.close()
        
        if success:
            # Mostra snackbar di successo
            self._show_snackbar(message)
            self.load_documents()
            self.update_doc_count()
        else:
            # Mostra errore
            QMessageBox.warning(
                self, 
                "Errore", 
                message
            )
    
    def _show_snackbar(self, message, duration=3000):
        """Mostra uno snackbar con il messaggio
        
        Args:
            message: Messaggio da mostrare
            duration: Durata in millisecondi (default: 3000)
        """
        # Crea snackbar
        snackbar = Snackbar(message, self, duration)
        
        # Posiziona in basso al centro
        snackbar_width = 400
        x = (self.width() - snackbar_width) // 2
        y = self.height() - 100
        
        snackbar.setFixedWidth(snackbar_width)
        snackbar.move(x, y)
        snackbar.show_animated()
    
    def delete_document(self, doc_id):
        """Elimina un documento dalla lista (non dal disco)"""
        reply = QMessageBox.question(
            self,
            "Conferma Rimozione",
            "Sei sicuro di voler rimuovere questo documento dalla materia?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Rimuovi dal vector database prima di eliminare dal DB
            try:
                collection_name = self.rag_service.create_collection(
                    self.subject_data['id'],
                    self.subject_data['name']
                )
                self.rag_service.remove_document(collection_name, doc_id)
            except Exception as e:
                print(f"Errore rimozione da RAG: {e}")
                # Continua comunque con l'eliminazione dal DB
            
            try:
                # Rimuovi solo dal database, NON dal disco (delete_physical_file=False)
                result = self.db.delete_document(doc_id, delete_physical_file=False)
                if result:
                    # Mostra snackbar che si chiude dopo 1 secondo
                    self._show_snackbar("Documento rimosso!", duration=1000)
                    self.load_documents()
                    self.update_doc_count()
                else:
                    QMessageBox.warning(
                        self,
                        "Errore",
                        "Errore durante la rimozione"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Errore",
                    f"Errore durante la rimozione del documento: {e}"
                )
    
    def update_doc_count(self):
        """Aggiorna il contatore dei documenti"""
        documents = self.db.get_documents_by_subject(self.subject_data['id'])
        count = len(documents)
        self.doc_count_label.setText(f"Documenti disponibili: {count}")
    
    # ==================== GENERAZIONE FLASHCARD ====================
    
    def generate_flashcards(self):
        """Avvia la generazione delle flashcard con RAG e Reflection"""
        documents = self.db.get_documents_by_subject(self.subject_data['id'])
        
        if not documents:
            QMessageBox.warning(
                self,
                "Nessun Documento",
                "Carica almeno un documento prima di generare flashcard"
            )
            return
        
        # Verifica che i documenti abbiano contenuto
        has_content = any(doc.get('content') for doc in documents)
        if not has_content:
            QMessageBox.warning(
                self,
                "Contenuto Vuoto",
                "I documenti non contengono testo estraibile"
            )
            return
        
        # Mostra progress dialog con più dettagli
        progress = QProgressDialog(
            "Inizializzando generazione...", 
            "Annulla", 
            0, 
            100,  # Range 0-100 per percentuale
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Avvia il thread di generazione
        use_web_search = self.web_search_checkbox.isChecked()
        
        # Determina quale servizio AI utilizzare dalla configurazione
        use_local_llm = get_env_bool('USE_LOCAL_LLM', default=True)
        
        if use_local_llm:
            # Usa LLM locale (LM Studio, Ollama, etc.) con API OpenAI-like
            base_url = os.environ.get('LOCAL_LLM_BASE_URL', 'http://127.0.0.1:1234/v1')
            model = os.environ.get('LOCAL_LLM_MODEL', '')
            
            try:
                ai_service = LocalLLMService(
                    base_url=base_url,
                    model=model if model else None
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Errore LLM Locale",
                    f"Impossibile connettersi al server LLM locale su {base_url}.\n"
                    f"Assicurati che LM Studio o Ollama siano in esecuzione.\n\n"
                    f"Errore: {str(e)}"
                )
                return
        else:
            # Usa Google Gemini API
            api_key = os.environ.get('GEMINI_API_KEY', '')
            
            if not api_key:
                QMessageBox.warning(
                    self,
                    "API Key Mancante",
                    "Configura l'API Key di Google Gemini nel file .env prima di generare flashcard.\n\n"
                    "Apri il file .env e imposta:\n"
                    "GEMINI_API_KEY=la-tua-api-key"
                )
                return
            
            model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')
            ai_service = AIService(api_key, model_name)
        
        # Crea il servizio Reflection
        reflection_service = ReflectionService(ai_service)
        
        # Determina se usare RAG e Reflection (configurabile tramite env)
        use_rag = get_env_bool('USE_RAG', default=True)
        use_reflection = get_env_bool('USE_REFLECTION', default=True)
        
        # Ottieni la query utente dal campo di input (già caricata all'apertura della finestra)
        user_query = self.user_query_input.toPlainText().strip()
        
        # Crea il thread di generazione con i nuovi parametri
        self.generation_thread = GenerationThread(
            ai_service=ai_service,
            rag_service=self.rag_service,
            reflection_service=reflection_service,
            subject_id=self.subject_data['id'],
            subject_name=self.subject_data['name'],
            documents=documents,
            num_cards=int(self.num_cards_spin.value()),
            use_web_search=use_web_search,
            use_rag=use_rag,
            use_reflection=use_reflection,
            user_query=user_query,  # NUOVO PARAMETRO
            web_search_service=self.web_search_service,  # Passa servizio
        )
        
        # Connetti i segnali
        self.generation_thread.finished.connect(
            lambda cards: self.on_generation_complete(cards, progress)
        )
        self.generation_thread.error.connect(
            lambda title, msg: self.on_generation_error(title, msg, progress)
        )
        self.generation_thread.progress.connect(
            lambda pct, msg: self.on_generation_progress(progress, pct, msg)
        )
        
        progress.canceled.connect(self.generation_thread.terminate)
        self.generation_thread.start()
    
    def on_generation_progress(self, progress_dialog, percentage, message):
        """Aggiorna il progress dialog con i dettagli"""
        try:
            if progress_dialog and percentage is not None:
                progress_dialog.setValue(int(percentage))
            if progress_dialog and message:
                progress_dialog.setLabelText(str(message))
        except Exception as e:
            print(f"Errore nell'aggiornamento del progresso: {e}")
    
    def on_generation_complete(self, flashcards, progress):
        """Chiamata quando la generazione è completata"""
        progress.close()
        
        if not flashcards:
            QMessageBox.warning(
                self,
                "Nessuna Flashcard",
                "Non è stato possibile generare flashcard"
            )
            return
        
        # Salva le flashcard nel database
        for card in flashcards:
            self.db.create_flashcard(
                self.subject_data['id'],
                card['front'],
                card['back'],
                card.get('difficulty', 'medium')  # Default to 'medium' not 'medio'
            )
        
        QMessageBox.information(
            self,
            "Successo",
            f"Generate {len(flashcards)} flashcard!"
        )
        
        self.load_flashcards()
        self.tabs.setCurrentIndex(2)  # Passa al tab flashcard
    
    def on_generation_error(self, title, message, progress):
        """Chiamata in caso di errore durante la generazione"""
        progress.close()
        QMessageBox.critical(
            self,
            title,
            message
        )
    
    # ==================== GESTIONE FLASHCARD ====================
    
    def load_flashcards(self):
        """Carica le flashcard dal database"""
        self.flashcards = self.db.get_flashcards_by_subject(self.subject_data['id'])
        self.current_flashcard_index = 0
        self.is_flipped = False
        self.update_flashcard_display()
    
    def update_flashcard_display(self):
        """Aggiorna la visualizzazione della flashcard corrente"""
        if not self.flashcards:
            # Nascondi la card quando non ci sono flashcard
            self.flashcard_card.hide()
            self.flashcard_counter.setText("0 / 0")
            # Mostra solo un messaggio testuale senza la card
            self.hint_label.setText("Nessuna flashcard disponibile. Genera alcune flashcard dalla tab 'Genera'.")
            self.hint_label.show()
            return
        
        # Mostra la card se era nascosta
        self.flashcard_card.show()
        
        # Aggiorna contatore
        total = len(self.flashcards)
        current = self.current_flashcard_index + 1
        self.flashcard_counter.setText(f"{current} / {total}")
        
        # Mostra la flashcard corrente
        card = self.flashcards[self.current_flashcard_index]
        
        if self.is_flipped:
            # Processa LaTeX e usa setHtml per il rendering
            back_text = LaTeXService.process_text(card['back'])
            self.flashcard_label.setHtml(back_text)
            self.flashcard_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Ripristina allineamento
            
            self.hint_label.setText("Risposta")
            
            # Mostra difficoltà
            difficulty = card.get('difficulty', 'medium')
            
            # Mappa da inglese/italiano a inglese (per retrocompatibilità)
            difficulty_normalize = {
                'facile': 'easy',
                'easy': 'easy',
                'medio': 'medium',
                'medium': 'medium',
                'difficile': 'hard',
                'hard': 'hard'
            }
            difficulty_en = difficulty_normalize.get(difficulty.lower(), 'medium')
            
            # Mappa per visualizzazione in italiano
            difficulty_display = {
                'easy': 'Facile',
                'medium': 'Medio',
                'hard': 'Difficile'
            }
            
            # Recupera i colori del tema
            _, difficulty_colors = get_theme_colors()
            color = difficulty_colors.get(difficulty_en, difficulty_colors['medium'])
            
            self.difficulty_label.setText(difficulty_display.get(difficulty_en, 'Medio'))
            # Usa get_color_with_opacity()
            self.difficulty_label.setStyleSheet(f"""
                font-size: 14px;
                font-weight: 600;
                color: {color};
                background-color: {self.get_color_with_opacity(color, 0.15)}; 
                padding: 8px 16px;
                border-radius: 20px;
            """)
            self.difficulty_label.show()
        else:
            # Processa LaTeX e usa setHtml per il rendering
            front_text = LaTeXService.process_text(card['front'])
            self.flashcard_label.setHtml(front_text)
            self.flashcard_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Ripristina allineamento
            
            self.hint_label.setText("Clicca per vedere la risposta")
            self.difficulty_label.hide()
    
    def flip_card(self):
        """Gira la flashcard corrente"""
        if not self.flashcards:
            return
        
        self.is_flipped = not self.is_flipped
        self.update_flashcard_display()
    
    def previous_flashcard(self):
        """Passa alla flashcard precedente"""
        if self.current_flashcard_index > 0:
            self.current_flashcard_index -= 1
            self.is_flipped = False
            self.update_flashcard_display()
    
    def next_flashcard(self):
        """Passa alla flashcard successiva"""
        if self.current_flashcard_index < len(self.flashcards) - 1:
            self.current_flashcard_index += 1
            self.is_flipped = False
            self.update_flashcard_display()
    
    def edit_current_flashcard(self):
        """Apre il dialog per modificare la flashcard corrente"""
        if not self.flashcards:
            return
        
        card = self.flashcards[self.current_flashcard_index]
        dialog = EditFlashcardDialog(card, self)
        
        if dialog.exec():
            self.load_flashcards()
    
    def delete_current_flashcard(self):
        """Elimina la flashcard corrente"""
        if not self.flashcards:
            return
        
        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            "Sei sicuro di voler eliminare questa flashcard?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            card = self.flashcards[self.current_flashcard_index]
            
            try:
                self.db.delete_flashcard(card['id'])
                
                # Rimuovi la flashcard dalla lista
                self.flashcards.pop(self.current_flashcard_index)
                
                # Aggiorna l'indice
                if len(self.flashcards) == 0:
                    # Se non ci sono più flashcard, resetta l'indice
                    self.current_flashcard_index = 0
                elif self.current_flashcard_index >= len(self.flashcards):
                    # Se l'indice è fuori range, vai all'ultima flashcard
                    self.current_flashcard_index = len(self.flashcards) - 1
                
                # Reset del flip
                self.is_flipped = False
                
                # Aggiorna l'UI
                self.update_flashcard_display()
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Errore",
                    f"Errore durante l'eliminazione: {str(e)}"
                )
    
    def export_flashcards(self):
        """Esporta le flashcard in vari formati"""
        if not self.flashcards:
            QMessageBox.warning(
                self,
                "Nessuna Flashcard",
                "Non ci sono flashcard da esportare"
            )
            return
        
        # Chiedi formato di export
        export_service = ExportService()
        
        options = QFileDialog.Options()
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Esporta Flashcard",
            f"{self.subject_data['name']}_flashcards",
            "CSV (*.csv);;TSV (*.tsv);;APKG (*.apkg)",
            options=options
        )
        
        if not file_path:
            return
        
        try:
            # Assicurati che il file abbia l'estensione corretta
            if 'CSV' in selected_filter and not file_path.endswith('.csv'):
                file_path += '.csv'
            elif 'TSV' in selected_filter and not file_path.endswith('.tsv'):
                file_path += '.tsv'
            elif 'APKG' in selected_filter and not file_path.endswith('.apkg'):
                file_path += '.apkg'
            
            # Determina il formato in base al filtro selezionato
            if 'CSV' in selected_filter:
                export_service.export_to_csv(self.flashcards, file_path)
            elif 'TSV' in selected_filter:
                export_service.export_to_tsv(self.flashcards, file_path)
            elif 'APKG' in selected_filter:
                # Passa il nome della materia come nome del deck
                export_service.export_to_apkg(self.flashcards, file_path, self.subject_data['name'])
            
            QMessageBox.information(
                self,
                "Successo",
                "Flashcard esportate con successo!"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante l'esportazione: {str(e)}"
            )
    
    def apply_theme(self):
        """Applica lo stile del tema corrente alla finestra e ricarica tutti i widget"""
        self.setStyleSheet(get_theme_style())
        
        theme = self.db.get_setting('theme', 'light')
        
        current_tab = self.tabs.currentIndex()
        
        documents_icon = IconProvider.get_icon("document", 18, get_icon_color())
        generate_icon = IconProvider.get_icon("sparkles", 18, get_icon_color())
        flashcards_icon = IconProvider.get_icon("cards", 18, get_icon_color())
        
        self.tabs.setTabIcon(0, documents_icon)
        self.tabs.setTabIcon(1, generate_icon)
        self.tabs.setTabIcon(2, flashcards_icon)
        
        old_docs_tab = self.tabs.widget(0)
        self.documents_tab = self.create_documents_tab()
        self.tabs.removeTab(0)
        self.tabs.insertTab(0, self.documents_tab, documents_icon, "Documenti")
        old_docs_tab.deleteLater()
        
        old_gen_tab = self.tabs.widget(1)
        self.generate_tab = self.create_generate_tab()
        self.tabs.removeTab(1)
        self.tabs.insertTab(1, self.generate_tab, generate_icon, "Genera")
        old_gen_tab.deleteLater()
        
        old_flash_tab = self.tabs.widget(2)
        self.flashcards_tab = self.create_flashcards_tab()
        self.tabs.removeTab(2)
        self.tabs.insertTab(2, self.flashcards_tab, flashcards_icon, "Flashcard")
        old_flash_tab.deleteLater()
        
        self.tabs.setCurrentIndex(current_tab)
        
        self.load_data()
        
        self.update()
    
    def export_flashcards(self):
        """Esporta le flashcard in vari formati"""
        if not self.flashcards:
            QMessageBox.warning(
                self,
                "Nessuna Flashcard",
                "Non ci sono flashcard da esportare"
            )
            return
        
        # Chiedi formato di export
        export_service = ExportService()
        
        options = QFileDialog.Options()
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Esporta Flashcard",
            f"{self.subject_data['name']}_flashcards",
            "CSV (*.csv);;TSV (*.tsv);;APKG (*.apkg)",
            options=options
        )
        
        if not file_path:
            return
        
        try:
            # Assicurati che il file abbia l'estensione corretta
            if 'CSV' in selected_filter and not file_path.endswith('.csv'):
                file_path += '.csv'
            elif 'TSV' in selected_filter and not file_path.endswith('.tsv'):
                file_path += '.tsv'
            elif 'APKG' in selected_filter and not file_path.endswith('.apkg'):
                file_path += '.apkg'
            
            # Determina il formato in base al filtro selezionato
            if 'CSV' in selected_filter:
                export_service.export_to_csv(self.flashcards, file_path)
            elif 'TSV' in selected_filter:
                export_service.export_to_tsv(self.flashcards, file_path)
            elif 'APKG' in selected_filter:
                # Passa il nome della materia come nome del deck
                export_service.export_to_apkg(self.flashcards, file_path, self.subject_data['name'])
            
            QMessageBox.information(
                self,
                "Successo",
                "Flashcard esportate con successo!"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante l'esportazione: {str(e)}"
            )