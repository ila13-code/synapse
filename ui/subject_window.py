from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTabWidget, QFileDialog,
                             QScrollArea, QFrame, QGridLayout, QMessageBox,
                             QProgressDialog, QCheckBox,QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextOption
from database.db_manager import DatabaseManager
from services.file_service import FileService
from services.ai_service import AIService
from services.export_service import ExportService
from ui.styles import MAIN_STYLE
from ui.dialogs import EditFlashcardDialog
from ui.icons import IconProvider
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
    
    def get_color_with_opacity(self, hex_color, opacity=0.2):
        """Converte un colore hex in rgba con opacità specificata"""
        color = QColor(hex_color)
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {opacity})"
        
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
        
        # Tabs
        self.documents_tab = self.create_documents_tab()
        documents_icon = IconProvider.get_icon("document", 18, "#262626")
        self.tabs.addTab(self.documents_tab, "Documenti")
        self.tabs.setTabIcon(0, documents_icon)
        
        self.generate_tab = self.create_generate_tab()
        generate_icon = IconProvider.get_icon("sparkles", 18, "#262626")
        self.tabs.addTab(self.generate_tab, "Genera")
        self.tabs.setTabIcon(1, generate_icon)
        
        self.flashcards_tab = self.create_flashcards_tab()
        flashcards_icon = IconProvider.get_icon("cards", 18, "#262626")
        self.tabs.addTab(self.flashcards_tab, "Flashcard")
        self.tabs.setTabIcon(2, flashcards_icon)
        
        main_layout.addWidget(self.tabs)
    
    def create_header(self):
        """Crea l'header della finestra con informazioni sulla materia"""
        header = QWidget()
        header.setStyleSheet("""
            background-color: white; 
            border-bottom: 1px solid #E8E8E8;
        """)
        header.setFixedHeight(80)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # Pulsante indietro
        back_btn = QPushButton(" Indietro")
        back_btn.setIcon(IconProvider.get_icon("arrow-left", 16, "#262626"))
        back_btn.setProperty("class", "secondary")
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)
        
        # Info materia con indicatore colore
        info_layout = QHBoxLayout()
        info_layout.setSpacing(12)
        
        # Indicatore colore con opacità corretta
        color_indicator = QFrame()
        color_indicator.setFixedSize(40, 40)
        bg_color = self.get_color_with_opacity(self.subject_data['color'], 0.2)
        color_indicator.setStyleSheet(f"""
            background-color: {bg_color};
            border-radius: 10px;
        """)
        info_layout.addWidget(color_indicator)
        
        # Nome e descrizione
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        name_label = QLabel(self.subject_data['name'])
        name_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: 700; 
            color: #171717;
        """)
        text_layout.addWidget(name_label)
        
        if self.subject_data.get('description'):
            desc_label = QLabel(self.subject_data['description'])
            desc_label.setStyleSheet("""
                font-size: 13px; 
                color: #737373;
            """)
            text_layout.addWidget(desc_label)
        
        info_layout.addLayout(text_layout)
        layout.addLayout(info_layout)
        layout.addStretch()
        
        return header
    
    def create_documents_tab(self):
        """Tab per gestire i documenti della materia"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(24)
        
        # Card per upload documenti
        upload_card = self.create_upload_card()
        layout.addWidget(upload_card)
        
        # Header documenti
        self.docs_header = QLabel("Documenti Caricati (0)")
        self.docs_header.setStyleSheet("""
            font-size: 18px; 
            font-weight: 700; 
            color: #171717;
        """)
        layout.addWidget(self.docs_header)
        
        # ScrollArea per documenti
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        self.docs_layout = QVBoxLayout(scroll_content)
        self.docs_layout.setSpacing(12)
        self.docs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return widget
    
    def create_upload_card(self):
        """Crea la card per l'upload dei documenti"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
                border-radius: 16px;
            }
        """)
        card.setFixedHeight(180)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # Icona
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, "upload", 48, "#8B5CF6")
        layout.addWidget(icon_label)
        
        # Titolo
        title_label = QLabel("Carica Documenti")
        title_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: 600; 
            color: #171717;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Descrizione
        desc_label = QLabel("Carica file PDF o TXT per creare flashcard")
        desc_label.setStyleSheet("""
            font-size: 13px; 
            color: #737373;
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # Pulsante upload
        upload_btn = QPushButton("Seleziona File")
        upload_btn.setProperty("class", "primary")
        upload_btn.clicked.connect(self.upload_document)
        layout.addWidget(upload_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return card
    
    def create_document_card(self, doc):
        """Crea una card per visualizzare un documento"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
                border-radius: 12px;
            }
            QFrame:hover {
                background-color: #FAFAFA;
            }
        """)
        card.setFixedHeight(80)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Icona documento
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, "file_text", 32, "#8B5CF6")
        layout.addWidget(icon_label)
        
        # Info documento
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(doc['name'])
        name_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #171717;
        """)
        info_layout.addWidget(name_label)
        
        # Metadati (dimensione e data)
        size_text = self.file_service.format_file_size(doc['size_bytes'] or 0)
        date_text = doc['created_at'][:10]
        meta_label = QLabel(f"{size_text} • {date_text}")
        meta_label.setStyleSheet("""
            font-size: 12px; 
            color: #737373;
        """)
        info_layout.addWidget(meta_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Pulsante elimina
        delete_btn = QPushButton()
        delete_btn.setIcon(IconProvider.get_icon("trash", 18, "#EF4444"))
        delete_btn.setProperty("class", "icon-button")
        delete_btn.setFixedSize(36, 36)
        delete_btn.clicked.connect(lambda: self.delete_document(doc['id']))
        layout.addWidget(delete_btn)
        
        return card
    
    def create_generate_tab(self):
        """Tab per generare flashcard con AI"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(32)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Card principale generazione
        gen_card = QFrame()
        gen_card.setProperty("class", "card")
        gen_card.setFixedWidth(650)
        
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setContentsMargins(40, 40, 40, 40)
        gen_layout.setSpacing(24)
        
        # Icona principale
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, "sparkles", 64, "#8B5CF6")
        gen_layout.addWidget(icon_label)
        
        # Titolo
        title_label = QLabel("Genera Flashcard con AI")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: 700; 
            color: #171717;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_layout.addWidget(title_label)
        
        # Descrizione
        desc_label = QLabel(
            "L'AI analizzerà i tuoi documenti e creerà flashcard "
            "ottimizzate per il tuo apprendimento"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-size: 14px; 
            color: #737373;
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_layout.addWidget(desc_label)
        
        # Statistiche documenti
        self.doc_count_label = QLabel("Documenti disponibili: 0")
        self.doc_count_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #8B5CF6;
            background-color: #F8F8F8;
            padding: 16px;
            border: none;
            border-radius: 12px;
        """)
        self.doc_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gen_layout.addWidget(self.doc_count_label)
        
        # Opzione ricerca web
        web_search_frame = self.create_web_search_option()
        gen_layout.addWidget(web_search_frame)
        
        # Pulsante genera
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
        frame.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border: none;
                border-radius: 12px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Icona web
        web_icon = QLabel()
        IconProvider.setup_icon_label(web_icon, "globe", 24, "#3B82F6")
        layout.addWidget(web_icon)
        
        # Testo descrizione
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Ricerca Web")
        title.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #171717;
        """)
        text_layout.addWidget(title)
        
        desc = QLabel("Integra informazioni aggiornate dal web")
        desc.setStyleSheet("""
            font-size: 12px; 
            color: #737373;
        """)
        text_layout.addWidget(desc)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # Checkbox
        self.web_search_checkbox = QCheckBox()
        self.web_search_checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        layout.addWidget(self.web_search_checkbox)
        
        return frame
    
    def create_flashcards_tab(self):
        """Tab per visualizzare e gestire le flashcard"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Header con contatore
        header_layout = QHBoxLayout()
        
        self.flashcard_counter = QLabel("0 / 0")
        self.flashcard_counter.setStyleSheet("""
            font-size: 18px; 
            font-weight: 700; 
            color: #171717;
        """)
        header_layout.addWidget(self.flashcard_counter)
        header_layout.addStretch()
        
        # Pulsante esporta
        export_btn = QPushButton(" Esporta")
        export_btn.setIcon(IconProvider.get_icon("download", 18, "#262626"))
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(self.export_flashcards)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # Card flashcard principale
        self.flashcard_card = self.create_flashcard_display()
        layout.addWidget(self.flashcard_card, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Pulsanti azione (modifica, elimina)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        
        edit_btn = QPushButton(" Modifica")
        edit_btn.setIcon(IconProvider.get_icon("edit", 18, "#262626"))
        edit_btn.setProperty("class", "secondary")
        edit_btn.clicked.connect(self.edit_current_flashcard)
        action_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton(" Elimina")
        delete_btn.setIcon(IconProvider.get_icon("trash", 18, "#EF4444"))
        delete_btn.setProperty("class", "secondary")
        delete_btn.clicked.connect(self.delete_current_flashcard)
        action_layout.addWidget(delete_btn)
        
        layout.addLayout(action_layout)
        
        # Navigazione
        nav_layout = self.create_navigation_controls()
        layout.addLayout(nav_layout)
        
        return widget
    


    def create_flashcard_display(self):
        """Crea la card per visualizzare la flashcard corrente"""
        card = QFrame()
        card.setProperty("class", "flashcard")
        # Rimuovi setFixedSize(600, 350) per permettere la crescita verticale
        card.setFixedWidth(600) # Mantieni la larghezza fissa
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Evento click per girare la carta
        card.mousePressEvent = lambda e: self.flip_card()
        
        self.flashcard_layout = QVBoxLayout(card)
        self.flashcard_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flashcard_layout.setSpacing(20)
        
        # Contenuto principale: usa QTextEdit al posto di QLabel
        self.flashcard_label = QTextEdit("Nessuna flashcard disponibile")
        self.flashcard_label.setReadOnly(True) # Rendi non modificabile
        self.flashcard_label.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere) # Abilita word wrap
        self.flashcard_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.flashcard_label.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Stile per QTextEdit (deve replicare lo stile del QLabel precedente e rimuovere la cornice di default)
        self.flashcard_label.setStyleSheet("""
            QTextEdit {
                font-size: 20px; 
                color: #262626;
                background-color: transparent;
                border: none;
                padding: 0; 
                margin: 0;
            }
        """)
        # Aggiungi una dimensione minima per un aspetto migliore
        self.flashcard_label.setMinimumHeight(200)

        self.flashcard_layout.addWidget(self.flashcard_label)
        
        # Label difficoltà
        self.difficulty_label = QLabel()
        self.difficulty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.difficulty_label.hide()
        self.flashcard_layout.addWidget(self.difficulty_label)
        
        # Hint
        self.hint_label = QLabel("Clicca per girare la carta")
        self.hint_label.setStyleSheet("""
            font-size: 14px; 
            color: #737373; 
            margin-top: 20px;
        """)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flashcard_layout.addWidget(self.hint_label)
        
        return card


    def create_navigation_controls(self):
        """Crea i controlli di navigazione per le flashcard"""
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(12)
        
        # Precedente
        self.prev_btn = QPushButton(" Precedente")
        self.prev_btn.setIcon(IconProvider.get_icon("arrow-left", 16, "#262626"))
        self.prev_btn.setProperty("class", "secondary")
        self.prev_btn.setFixedWidth(150)
        self.prev_btn.clicked.connect(self.previous_flashcard)
        nav_layout.addWidget(self.prev_btn)
        
        # Gira carta
        flip_btn = QPushButton("Gira Carta")
        flip_btn.setProperty("class", "secondary")
        flip_btn.setFixedWidth(150)
        flip_btn.clicked.connect(self.flip_card)
        nav_layout.addWidget(flip_btn)
        
        # Successivo
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
        # Pulisci layout esistente
        while self.docs_layout.count():
            child = self.docs_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Recupera documenti dal database
        documents = self.db.get_documents_by_subject(self.subject_data['id'])
        
        # Aggiorna header
        self.docs_header.setText(f"Documenti Caricati ({len(documents)})")
        
        # Mostra messaggio se vuoto
        if not documents:
            empty_label = QLabel("Nessun documento caricato ancora")
            empty_label.setStyleSheet("""
                font-size: 14px; 
                color: #737373; 
                padding: 40px;
            """)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.docs_layout.addWidget(empty_label)
            return
        
        # Crea card per ogni documento
        for doc in documents:
            doc_card = self.create_document_card(doc)
            self.docs_layout.addWidget(doc_card)
    
    def upload_document(self):
        """Gestisce l'upload di un nuovo documento"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona Documento",
            "",
            "Documenti (*.txt *.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            # Salva il documento
            doc_id = self.file_service.save_document(
                file_path, 
                self.subject_data['id']
            )
            
            if doc_id:
                QMessageBox.information(
                    self, 
                    "Successo", 
                    "Documento caricato con successo!"
                )
                self.load_documents()
                self.update_doc_count()
            else:
                QMessageBox.warning(
                    self, 
                    "Errore", 
                    "Errore durante il caricamento del documento"
                )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Errore", 
                f"Errore: {str(e)}"
            )
    
    def delete_document(self, doc_id):
        """Elimina un documento"""
        reply = QMessageBox.question(
            self,
            "Conferma Eliminazione",
            "Sei sicuro di voler eliminare questo documento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_document(doc_id):
                QMessageBox.information(
                    self, 
                    "Successo", 
                    "Documento eliminato!"
                )
                self.load_documents()
                self.update_doc_count()
            else:
                QMessageBox.warning(
                    self, 
                    "Errore", 
                    "Errore durante l'eliminazione"
                )
    
    def update_doc_count(self):
        """Aggiorna il contatore dei documenti"""
        documents = self.db.get_documents_by_subject(self.subject_data['id'])
        count = len(documents)
        self.doc_count_label.setText(f"Documenti disponibili: {count}")
    
    # ==================== GENERAZIONE FLASHCARD ====================
    
    def generate_flashcards(self):
        """Avvia la generazione delle flashcard"""
        documents = self.db.get_documents_by_subject(self.subject_data['id'])
        
        if not documents:
            QMessageBox.warning(
                self,
                "Nessun Documento",
                "Carica almeno un documento prima di generare flashcard"
            )
            return
        
        # Estrai contenuto dai documenti
        all_content = []
        for doc in documents:
            if doc['content']:
                all_content.append(doc['content'])
        
        if not all_content:
            QMessageBox.warning(
                self,
                "Contenuto Vuoto",
                "I documenti non contengono testo estraibile"
            )
            return
        
        # Combina il contenuto
        combined_content = "\n\n".join(all_content)
        
        # Mostra progress dialog
        progress = QProgressDialog(
            "Generazione flashcard in corso...", 
            "Annulla", 
            0, 
            0, 
            self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Avvia il thread di generazione
        use_web_search = self.web_search_checkbox.isChecked()
        ai_service = AIService()
        
        self.generation_thread = GenerationThread(
            ai_service,
            combined_content,
            num_cards=10,
            use_web_search=use_web_search
        )
        
        self.generation_thread.finished.connect(
            lambda cards: self.on_generation_complete(cards, progress)
        )
        self.generation_thread.error.connect(
            lambda error: self.on_generation_error(error, progress)
        )
        
        progress.canceled.connect(self.generation_thread.terminate)
        self.generation_thread.start()
    
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
                card.get('difficulty', 'medio')
            )
        
        QMessageBox.information(
            self,
            "Successo",
            f"Generate {len(flashcards)} flashcard!"
        )
        
        self.load_flashcards()
        self.tabs.setCurrentIndex(2)  # Passa al tab flashcard
    
    def on_generation_error(self, error, progress):
        """Chiamata in caso di errore durante la generazione"""
        progress.close()
        QMessageBox.critical(
            self,
            "Errore",
            f"Errore durante la generazione: {error}"
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
            self.flashcard_label.setText("Nessuna flashcard disponibile")
            self.difficulty_label.hide()
            self.hint_label.setText("Genera flashcard per iniziare")
            self.flashcard_counter.setText("0 / 0")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        
        # Aggiorna contatore
        total = len(self.flashcards)
        current = self.current_flashcard_index + 1
        self.flashcard_counter.setText(f"{current} / {total}")
        
        # Mostra la flashcard corrente
        card = self.flashcards[self.current_flashcard_index]
        
        if self.is_flipped:
            self.flashcard_label.setText(card['back'])
            self.hint_label.setText("Risposta")
            
            # Mostra difficoltà
            difficulty = card.get('difficulty', 'medio')
            difficulty_colors = {
                'facile': '#10B981',
                'medio': '#F59E0B',
                'difficile': '#EF4444'
            }
            
            color = difficulty_colors.get(difficulty, '#F59E0B')
            
            self.difficulty_label.setText(difficulty.capitalize())
            self.difficulty_label.setStyleSheet(f"""
                font-size: 14px;
                font-weight: 600;
                color: {color};
                background-color: {self.get_color_with_opacity(color, 0.1)};
                padding: 8px 16px;
                border-radius: 20px;
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
            
            if self.db.delete_flashcard(card['id']):
                QMessageBox.information(
                    self,
                    "Successo",
                    "Flashcard eliminata!"
                )
                
                # Ricarica e aggiusta l'indice
                self.flashcards.pop(self.current_flashcard_index)
                if self.current_flashcard_index >= len(self.flashcards):
                    self.current_flashcard_index = max(0, len(self.flashcards) - 1)
                
                self.is_flipped = False
                self.update_flashcard_display()
            else:
                QMessageBox.warning(
                    self,
                    "Errore",
                    "Errore durante l'eliminazione"
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
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Esporta Flashcard",
            f"{self.subject_data['name']}_flashcards",
            "PDF (*.pdf);;CSV (*.csv);;Anki (*.txt)"
        )
        
        if not file_path:
            return
        
        try:
            # Determina il formato in base al filtro selezionato
            if 'PDF' in selected_filter:
                export_service.export_to_pdf(self.flashcards, file_path)
            elif 'CSV' in selected_filter:
                export_service.export_to_csv(self.flashcards, file_path)
            elif 'Anki' in selected_filter:
                export_service.export_to_anki(self.flashcards, file_path)
            
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