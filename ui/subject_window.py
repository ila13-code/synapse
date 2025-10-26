from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTabWidget, QFileDialog,
                             QScrollArea, QFrame, QGridLayout, QMessageBox,
                             QProgressDialog, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from database.db_manager import DatabaseManager
from services.file_service import FileService
from services.ai_service import AIService
from services.export_service import ExportService
from ui.styles import MAIN_STYLE
from ui.dialogs import EditFlashcardDialog
import os

class GenerationThread(QThread):
    """Thread per generare flashcard senza bloccare l'UI"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, ai_service, content, num_cards=10, use_web_search=False):
        super().__init__()
        self.ai_service = ai_service
        self.content = content
        self.num_cards = num_cards
        self.use_web_search = use_web_search
    
    def run(self):
        try:
            flashcards = self.ai_service.generate_flashcards(
                self.content, 
                self.num_cards,
                self.use_web_search
            )
            self.finished.emit(flashcards)
        except Exception as e:
            self.error.emit(str(e))
class SubjectWindow(QMainWindow):
    def __init__(self, subject_data, parent=None):
        super().__init__(parent)
        self.subject_data = subject_data
        self.db = DatabaseManager()
        self.file_service = FileService()
        self.current_flashcard_index = 0
        self.is_flipped = False
        self.flashcards = []
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        self.setWindowTitle(f"Synapse - {self.subject_data['name']}")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(MAIN_STYLE)
        
        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # Tab Documenti
        self.documents_tab = self.create_documents_tab()
        self.tabs.addTab(self.documents_tab, "📄 Documenti")
        
        # Tab Genera
        self.generate_tab = self.create_generate_tab()
        self.tabs.addTab(self.generate_tab, "✨ Genera")
        
        # Tab Flashcard
        self.flashcards_tab = self.create_flashcards_tab()
        self.tabs.addTab(self.flashcards_tab, "📚 Flashcard")
        
        main_layout.addWidget(self.tabs)
        
    def create_header(self):
        """Crea l'header della finestra"""
        header = QWidget()
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #E8E8E8;")
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # Pulsante indietro
        back_btn = QPushButton("← Indietro")
        back_btn.setProperty("class", "secondary")
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)
        
        # Info materia
        info_layout = QHBoxLayout()
        info_layout.setSpacing(12)
        
        # Color indicator
        color_frame = QFrame()
        color_frame.setFixedSize(40, 40)
        color_frame.setStyleSheet(f"""
            background-color: {self.subject_data['color']}30;
            border-radius: 10px;
        """)
        info_layout.addWidget(color_frame)
        
        # Nome e descrizione
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        name_label = QLabel(self.subject_data['name'])
        name_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #171717;")
        text_layout.addWidget(name_label)
        
        if self.subject_data.get('description'):
            desc_label = QLabel(self.subject_data['description'])
            desc_label.setStyleSheet("font-size: 13px; color: #737373;")
            text_layout.addWidget(desc_label)
        
        info_layout.addLayout(text_layout)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        return header
    
    def create_documents_tab(self):
        """Tab per gestire i documenti"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # Card upload
        upload_card = QFrame()
        upload_card.setStyleSheet("""
            QFrame {
                background-color: white; /* Sfondo bianco */
                border: none; /* NESSUN BORDO */
                border-radius: 16px;
            }
        """)
        upload_card.setFixedHeight(200)
        
        upload_layout = QVBoxLayout(upload_card)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.setSpacing(16)
        
        icon_label = QLabel("📤")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(icon_label)
        
        title_label = QLabel("Carica Documenti")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #262626;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(title_label)
        
        desc_label = QLabel("Supporta file TXT e PDF (max 10MB)")
        desc_label.setStyleSheet("font-size: 13px; color: #737373;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_layout.addWidget(desc_label)
        
        upload_btn = QPushButton("Seleziona File")
        upload_btn.setProperty("class", "primary")
        upload_btn.clicked.connect(self.upload_document)
        upload_layout.addWidget(upload_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(upload_card)
        
        # Lista documenti
        self.docs_header = QLabel(f"Documenti Caricati (0)")
        self.docs_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #171717;")
        layout.addWidget(self.docs_header)
        
        self.docs_scroll = QScrollArea()
        self.docs_scroll.setWidgetResizable(True)
        self.docs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.docs_container = QWidget()
        self.docs_layout = QVBoxLayout(self.docs_container)
        self.docs_layout.setSpacing(12)
        self.docs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.docs_scroll.setWidget(self.docs_container)
        layout.addWidget(self.docs_scroll)
        
        return widget
    
    def create_document_card(self, doc):
        """Crea una card per un documento"""
        card = QFrame()
        card.setProperty("class", "card")
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Icona
        icon_label = QLabel("📄")
        icon_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(icon_label)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(doc['name'])
        name_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #171717;")
        info_layout.addWidget(name_label)
        
        size_date = f"{self.file_service.format_file_size(doc['size_bytes'] or 0)} • {doc['created_at'][:10]}"
        meta_label = QLabel(size_date)
        meta_label.setStyleSheet("font-size: 12px; color: #737373;")
        info_layout.addWidget(meta_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Pulsante elimina
        delete_btn = QPushButton("🗑️")
        delete_btn.setProperty("class", "icon-button")
        delete_btn.clicked.connect(lambda: self.delete_document(doc['id']))
        layout.addWidget(delete_btn)
        
        return card
    
    def create_generate_tab(self):
        """Tab per generare flashcard"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Card generazione
        gen_card = QFrame()
        gen_card.setProperty("class", "card")
        gen_card.setFixedWidth(650)
        
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setContentsMargins(40, 40, 40, 40)
        gen_layout.setSpacing(24)
        
        # Icona
        icon_label = QLabel("✨")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_layout.addWidget(icon_label)
        
        # Titolo
        title_label = QLabel("Genera Flashcard con AI")
        title_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #171717;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_layout.addWidget(title_label)
        
        # Descrizione
        desc_label = QLabel("L'AI analizzerà i tuoi documenti e creerà flashcard ottimizzate per il tuo apprendimento")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; color: #737373;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_layout.addWidget(desc_label)
        
        # Stats
        self.doc_count_label = QLabel(f"📄 Documenti disponibili: 0")
        self.doc_count_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #8B5CF6;
            background-color: #F3F4F6;
            padding: 16px;
            border-radius: 12px;
        """)
        self.doc_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_layout.addWidget(self.doc_count_label)
        
        # NUOVO: Checkbox ricerca web
        web_search_frame = QFrame()
        web_search_frame.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
        """)
        
        web_search_layout = QHBoxLayout(web_search_frame)
        web_search_layout.setContentsMargins(20, 16, 20, 16)
        web_search_layout.setSpacing(12)
        
        # Icona
        web_icon = QLabel("🌐")
        web_icon.setStyleSheet("font-size: 24px;")
        web_icon.setFixedSize(32, 32)
        web_search_layout.addWidget(web_icon)
        
        # Testo
        web_text_layout = QVBoxLayout()
        web_text_layout.setSpacing(4)
        
        web_title = QLabel("Ricerca Web")
        web_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #171717;")
        web_text_layout.addWidget(web_title)
        
        web_desc = QLabel("Consenti a Gemini di usare la sua conoscenza generale per integrare i documenti")
        web_desc.setWordWrap(True)
        web_desc.setStyleSheet("font-size: 12px; color: #6B7280;")
        web_text_layout.addWidget(web_desc)
        
        web_search_layout.addLayout(web_text_layout, 1)  # stretch factor = 1
        
        # Checkbox
        self.web_search_checkbox = QCheckBox()
        self.web_search_checkbox.setChecked(False)
        self.web_search_checkbox.setFixedSize(28, 28)
        self.web_search_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
            }
            QCheckBox::indicator {
                width: 28px;
                height: 28px;
                border-radius: 6px;
                border: 2px solid #D1D5DB;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #8B5CF6;
                border-color: #8B5CF6;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjMzMzMgNC4wMDAwMUw2LjAwMDAxIDExLjMzMzNMMi42NjY2NyA4LjAwMDAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            QCheckBox::indicator:hover {
                border-color: #8B5CF6;
            }
        """)
        web_search_layout.addWidget(self.web_search_checkbox)
        
        gen_layout.addWidget(web_search_frame)
        
        # Pulsante genera
        self.generate_btn = QPushButton("✨ Genera Flashcard")
        self.generate_btn.setProperty("class", "primary")
        self.generate_btn.setFixedHeight(50)
        self.generate_btn.clicked.connect(self.generate_flashcards)
        gen_layout.addWidget(self.generate_btn)
        
        warning_label = QLabel("Carica prima alcuni documenti nella sezione 'Documenti'")
        warning_label.setStyleSheet("font-size: 12px; color: #737373;")
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_layout.addWidget(warning_label)
        
        layout.addWidget(gen_card)
        
        return widget

    def create_flashcards_tab(self):
        """Tab per visualizzare le flashcard"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # Header con contatore ed export
        header_layout = QHBoxLayout()
        
        self.flashcard_count_label = QLabel(f"Flashcard 0 di 0")
        self.flashcard_count_label.setStyleSheet("font-size: 14px; color: #737373;")
        header_layout.addWidget(self.flashcard_count_label)
        
        header_layout.addStretch()
        
        # Pulsante export
        export_btn = QPushButton("💾 Esporta CSV")
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(lambda: self.export_flashcards('csv'))
        header_layout.addWidget(export_btn)
        
        export_tsv_btn = QPushButton("💾 Esporta TSV")
        export_tsv_btn.setProperty("class", "secondary")
        export_tsv_btn.clicked.connect(lambda: self.export_flashcards('tsv'))
        header_layout.addWidget(export_tsv_btn)
        
        layout.addLayout(header_layout)
        
        # Card flashcard
        self.flashcard_card = QFrame()
        self.flashcard_card.setProperty("class", "card")
        self.flashcard_card.setFixedSize(800, 400)
        self.flashcard_card.setCursor(Qt.CursorShape.PointingHandCursor)
        self.flashcard_card.mousePressEvent = lambda e: self.flip_card()
        
        self.flashcard_layout = QVBoxLayout(self.flashcard_card)
        self.flashcard_layout.setContentsMargins(40, 40, 40, 40)
        self.flashcard_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Label per il contenuto
        self.flashcard_label = QLabel("Nessuna flashcard disponibile")
        self.flashcard_label.setWordWrap(True)
        self.flashcard_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flashcard_label.setStyleSheet("font-size: 20px; color: #262626;")
        self.flashcard_layout.addWidget(self.flashcard_label)
        
        # Label per difficoltà
        self.difficulty_label = QLabel()
        self.difficulty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.difficulty_label.hide()
        self.flashcard_layout.addWidget(self.difficulty_label)
        
        # Hint label
        self.hint_label = QLabel("Clicca per girare la carta")
        self.hint_label.setStyleSheet("font-size: 14px; color: #737373; margin-top: 20px;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flashcard_layout.addWidget(self.hint_label)
        
        layout.addWidget(self.flashcard_card, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Pulsanti azione
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        
        edit_btn = QPushButton("✏️ Modifica")
        edit_btn.setProperty("class", "secondary")
        edit_btn.clicked.connect(self.edit_current_flashcard)
        action_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Elimina")
        delete_btn.setProperty("class", "secondary")
        delete_btn.clicked.connect(self.delete_current_flashcard)
        action_layout.addWidget(delete_btn)
        
        layout.addLayout(action_layout)
        
        # Navigazione
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(12)
        
        self.prev_btn = QPushButton("◀ Precedente")
        self.prev_btn.setProperty("class", "secondary")
        self.prev_btn.setFixedWidth(150)
        self.prev_btn.clicked.connect(self.previous_flashcard)
        nav_layout.addWidget(self.prev_btn)
        
        flip_btn = QPushButton("🔄 Gira Carta")
        flip_btn.setProperty("class", "secondary")
        flip_btn.setFixedWidth(150)
        flip_btn.clicked.connect(self.flip_card)
        nav_layout.addWidget(flip_btn)
        
        self.next_btn = QPushButton("Successivo ▶")
        self.next_btn.setProperty("class", "secondary")
        self.next_btn.setFixedWidth(150)
        self.next_btn.clicked.connect(self.next_flashcard)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        return widget
    
    def load_data(self):
        """Carica tutti i dati"""
        self.load_documents()
        self.load_flashcards()
        self.update_doc_count()
    
    def load_documents(self):
        """Carica e visualizza i documenti"""
        # Pulisci layout
        while self.docs_layout.count():
            child = self.docs_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        documents = self.db.get_documents_by_subject(self.subject_data['id'])
        
        # Aggiorna header
        self.docs_header.setText(f"Documenti Caricati ({len(documents)})")
        
        if not documents:
            empty_label = QLabel("Nessun documento caricato ancora")
            empty_label.setStyleSheet("font-size: 14px; color: #737373; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.docs_layout.addWidget(empty_label)
            return
        
        for doc in documents:
            doc_card = self.create_document_card(doc)
            self.docs_layout.addWidget(doc_card)
    
    def upload_document(self):
        """Carica un nuovo documento"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona Documento",
            "",
            "Documenti (*.txt *.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            # Verifica dimensione
            size = self.file_service.get_file_size(file_path)
            if size > 10 * 1024 * 1024:  # 10MB
                QMessageBox.warning(self, "Errore", "Il file è troppo grande (max 10MB)")
                return
            
            # Estrai contenuto
            content = self.file_service.extract_text(file_path)
            
            # Salva nel database
            file_name = os.path.basename(file_path)
            file_type = self.file_service.get_file_type(file_path)
            
            self.db.create_document(
                self.subject_data['id'],
                file_name,
                file_path,
                file_type,
                content,
                size
            )
            
            QMessageBox.information(self, "Successo", "Documento caricato con successo!")
            self.load_documents()
            self.update_doc_count()
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel caricamento del documento: {e}")
    
    def delete_document(self, doc_id):
        """Elimina un documento"""
        reply = QMessageBox.question(
            self,
            "Conferma",
            "Sei sicuro di voler eliminare questo documento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_document(doc_id)
                self.load_documents()
                self.update_doc_count()
                QMessageBox.information(self, "Successo", "Documento eliminato")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore nell'eliminazione: {e}")
    
    def update_doc_count(self):
        """Aggiorna il contatore dei documenti"""
        count = self.db.get_document_count(self.subject_data['id'])
        self.doc_count_label.setText(f"📄 Documenti disponibili: {count}")

    def generate_flashcards(self):
        """Genera flashcard dai documenti usando AI"""
        # Verifica API key
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            QMessageBox.warning(
                self,
                "API Key Mancante",
                "Configura la tua Gemini API key nelle Impostazioni"
            )
            return
        
        # Verifica documenti
        documents = self.db.get_documents_by_subject(self.subject_data['id'])
        if not documents:
            QMessageBox.warning(self, "Errore", "Carica almeno un documento prima di generare flashcard")
            return
        
        # Combina contenuti
        content = "\n\n".join([doc['content'] for doc in documents if doc['content']])
        
        if not content.strip():
            QMessageBox.warning(self, "Errore", "Nessun contenuto trovato nei documenti")
            return
        
        # Verifica se usare la ricerca web
        use_web_search = self.web_search_checkbox.isChecked()
        
        # Progress dialog
        progress = QProgressDialog("Generazione flashcard in corso...", "Annulla", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setWindowTitle("Generazione AI")
        progress.setCancelButton(None)
        progress.show()
        
        # Crea AI service
        ai_service = AIService(api_key)
        
        # Genera in thread - PASSA use_web_search
        self.gen_thread = GenerationThread(ai_service, content, 10, use_web_search)
        self.gen_thread.finished.connect(lambda cards: self.on_generation_finished(cards, progress))
        self.gen_thread.error.connect(lambda err: self.on_generation_error(err, progress))
        self.gen_thread.start()

    def on_generation_finished(self, flashcards, progress):
        """Callback quando la generazione è completata"""
        progress.close()
        
        if not flashcards:
            QMessageBox.warning(self, "Errore", "Nessuna flashcard generata")
            return
        
        try:
            # Salva nel database
            cards_data = [
                {
                    'subject_id': self.subject_data['id'],
                    'front': card['front'],
                    'back': card['back'],
                    'difficulty': card['difficulty']
                }
                for card in flashcards
            ]
            
            self.db.create_flashcards_bulk(cards_data)
            
            QMessageBox.information(
                self,
                "Successo",
                f"Generate {len(flashcards)} flashcard con successo!"
            )
            
            self.load_flashcards()
            self.tabs.setCurrentIndex(2)  # Vai al tab flashcard
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel salvataggio: {e}")
    
    def on_generation_error(self, error, progress):
        """Callback quando c'è un errore nella generazione"""
        progress.close()
        QMessageBox.critical(self, "Errore", f"Errore nella generazione: {error}")

    def load_flashcards(self):
        """Carica le flashcard"""
        self.flashcards = self.db.get_flashcards_by_subject(self.subject_data['id'])
        self.current_flashcard_index = 0
        self.is_flipped = False
        self.update_flashcard_display()
    

    def update_flashcard_display(self):
        """Aggiorna la visualizzazione della flashcard corrente"""
        if not self.flashcards:
            self.flashcard_label.setText("Nessuna flashcard disponibile\n\nVai nella sezione 'Genera' per creare flashcard")
            self.flashcard_count_label.setText("Flashcard 0 di 0")
            self.difficulty_label.hide()
            self.hint_label.hide()
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            # Ripristina stile base (usa lo stile QFrame.card generale)
            self.flashcard_card.setStyleSheet("")
            return
        
        card = self.flashcards[self.current_flashcard_index]
        
        # Aggiorna contatore
        self.flashcard_count_label.setText(
            f"Flashcard {self.current_flashcard_index + 1} di {len(self.flashcards)}"
        )
        
        # Reset dello stile della card (usa lo stile QFrame.card generale)
        self.flashcard_card.setStyleSheet("")
        
        # Mostra fronte o retro
        if self.is_flipped:
            self.flashcard_label.setText(card['back'])
            self.hint_label.setText("")
            
            # Mostra difficoltà
            diff = card.get('difficulty', 'medium')
            diff_text = {'easy': 'Facile', 'medium': 'Medio', 'hard': 'Difficile'}
            # Assicurati che DIFFICULTY_COLORS sia importato correttamente
            diff_color = DIFFICULTY_COLORS.get(diff, '#8B5CF6') 
            
            # NUOVO: Applica lo stile colorato alla card GIRATA
            self.flashcard_card.setStyleSheet(f"""
                QFrame.card {{
                    background-color: {diff_color}10; /* Sfondo leggerissimo */
                    border: 2px solid {diff_color}; /* Bordo con colore difficoltà */
                    border-radius: 16px;
                }}
                QFrame.card:hover {{
                    border-color: {diff_color};
                }}
            """)
            
            self.difficulty_label.setText(diff_text[diff])
            self.difficulty_label.setStyleSheet(f"""
                font-size: 12px;
                font-weight: 600;
                color: {diff_color};
                background-color: {diff_color}20; /* Sfondo leggero per la label */
                padding: 6px 12px;
                border-radius: 6px;
                margin-top: 16px;
            """)
            self.difficulty_label.show()
        else:
            self.flashcard_label.setText(card['front'])
            self.hint_label.setText("Clicca per vedere la risposta")
            self.difficulty_label.hide()
        
        # Abilita/disabilita pulsanti navigazione
        self.prev_btn.setEnabled(self.current_flashcard_index > 0)
        self.next_btn.setEnabled(self.current_flashcard_index < len(self.flashcards) - 1)
        """Aggiorna la visualizzazione della flashcard corrente"""
        if not self.flashcards:
            self.flashcard_label.setText("Nessuna flashcard disponibile\n\nVai nella sezione 'Genera' per creare flashcard")
            self.flashcard_count_label.setText("Flashcard 0 di 0")
            self.difficulty_label.hide()
            self.hint_label.hide()
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            # Ripristina stile base
            self.flashcard_card.setStyleSheet("")
            return
        
        card = self.flashcards[self.current_flashcard_index]
        
        # Aggiorna contatore
        self.flashcard_count_label.setText(
            f"Flashcard {self.current_flashcard_index + 1} di {len(self.flashcards)}"
        )
        
        # Reset dello stile della card (usa lo stile generico QFrame.card di default)
        self.flashcard_card.setStyleSheet("")
        
        # Mostra fronte o retro
        if self.is_flipped:
            self.flashcard_label.setText(card['back'])
            self.hint_label.setText("")
            
            # Mostra difficoltà
            diff = card.get('difficulty', 'medium')
            diff_text = {'easy': 'Facile', 'medium': 'Medio', 'hard': 'Difficile'}
            diff_color = DIFFICULTY_COLORS.get(diff, '#8B5CF6') # Colore in base alla difficoltà
            
            # NUOVO: Applica lo stile colorato alla card
            self.flashcard_card.setStyleSheet(f"""
                QFrame.card {{
                    background-color: {diff_color}10; /* Sfondo molto leggero */
                    border: 2px solid {diff_color}; /* Bordo con colore difficoltà */
                    border-radius: 16px;
                }}
                QFrame.card:hover {{
                    border-color: {diff_color};
                }}
            """)
            
            self.difficulty_label.setText(diff_text[diff])
            self.difficulty_label.setStyleSheet(f"""
                font-size: 12px;
                font-weight: 600;
                color: {diff_color};
                background-color: {diff_color}20;
                padding: 6px 12px;
                border-radius: 6px;
                margin-top: 16px;
            """)
            self.difficulty_label.show()
        else:
            self.flashcard_label.setText(card['front'])
            self.hint_label.setText("Clicca per vedere la risposta")
            self.difficulty_label.hide()
        
        # Abilita/disabilita pulsanti navigazione
        self.prev_btn.setEnabled(self.current_flashcard_index > 0)
        self.next_btn.setEnabled(self.current_flashcard_index < len(self.flashcards) - 1)
    def flip_card(self):
        """Gira la flashcard"""
        if not self.flashcards:
            return
        
        self.is_flipped = not self.is_flipped
        self.update_flashcard_display()
    
    def next_flashcard(self):
        """Vai alla flashcard successiva"""
        if self.current_flashcard_index < len(self.flashcards) - 1:
            self.current_flashcard_index += 1
            self.is_flipped = False
            self.update_flashcard_display()
    
    def previous_flashcard(self):
        """Vai alla flashcard precedente"""
        if self.current_flashcard_index > 0:
            self.current_flashcard_index -= 1
            self.is_flipped = False
            self.update_flashcard_display()
    
    def edit_current_flashcard(self):
        """Modifica la flashcard corrente"""
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
            "Conferma",
            "Sei sicuro di voler eliminare questa flashcard?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                card = self.flashcards[self.current_flashcard_index]
                self.db.delete_flashcard(card['id'])
                QMessageBox.information(self, "Successo", "Flashcard eliminata")
                self.load_flashcards()
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore nell'eliminazione: {e}")
    
    def export_flashcards(self, format_type):
        """Esporta le flashcard"""
        if not self.flashcards:
            QMessageBox.warning(self, "Errore", "Nessuna flashcard da esportare")
            return
        
        filter_str = ExportService.get_export_filter(format_type)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Esporta Flashcard",
            f"flashcards_{self.subject_data['name']}.{format_type}",
            filter_str
        )
        
        if not file_path:
            return
        
        try:
            export_service = ExportService()
            if format_type == 'csv':
                export_service.export_to_csv(self.flashcards, file_path)
            elif format_type == 'tsv':
                export_service.export_to_tsv(self.flashcards, file_path)
            
            QMessageBox.information(self, "Successo", "Flashcard esportate con successo!")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'esportazione: {e}")