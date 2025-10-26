from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QScrollArea, QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont
from database.db_manager import DatabaseManager
from ui.styles import MAIN_STYLE
from ui.dialogs import CreateSubjectDialog, SettingsDialog
from ui.subject_window import SubjectWindow

class SubjectCard(QFrame):
    """Widget per visualizzare una card materia"""
    
    def __init__(self, subject_data, parent=None):
        super().__init__(parent)
        self.subject_data = subject_data
        self.parent_window = parent
        self.setup_ui()
        
    def setup_ui(self):
        accent_color = self.subject_data['color']
        self.setFixedSize(280, 200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Stile: Bordo sinistro colorato, background bianco.
        # Nessun background o bordo in hover (tranne l'accento) per pulizia.
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white; /* Sfondo sempre bianco */
                border: 1px solid #E8E8E8;
                border-left: 6px solid {accent_color}; /* Accentazione del colore */
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {accent_color}; 
                border-left: 6px solid {accent_color}; 
                background-color: white; 
            }}
            
            /* NUOVO: Rimuove i bordi e background bianchi dai QLabel interni */
            QLabel.card_text {{
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8) # Ridotto lo spacing per un layout più compatto
        
        # Icona Materia
        icon_label = QLabel("📚")
        icon_label.setStyleSheet(f"font-size: 28px; color: {accent_color};")
        layout.addWidget(icon_label)
        
        # Spacer
        layout.addStretch()
        
        # Nome materia (Label pulita)
        name_label = QLabel(self.subject_data['name'])
        name_label.setWordWrap(True)
        name_label.setProperty("class", "card_text") # Aggiunge la classe per lo stile pulito
        name_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #171717;")
        layout.addWidget(name_label)
        
        # Descrizione (Label pulita)
        if self.subject_data.get('description'):
            desc_label = QLabel(self.subject_data['description'])
            desc_label.setWordWrap(True)
            desc_label.setProperty("class", "card_text") # Aggiunge la classe per lo stile pulito
            desc_label.setStyleSheet("font-size: 13px; color: #525252;")
            layout.addWidget(desc_label)
        
        # Spazio aggiuntivo se non c'è descrizione
        if not self.subject_data.get('description'):
             layout.addSpacing(18) # Aggiungi spazio per bilanciare il layout
        
        # Data creazione (Label pulita)
        date_label = QLabel(f"Creata il {self.subject_data['created_at'][:10]}")
        date_label.setProperty("class", "card_text") # Aggiunge la classe per lo stile pulito
        date_label.setStyleSheet("font-size: 11px; color: #A3A3A3;")
        layout.addWidget(date_label)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_subject()
            
    def open_subject(self):
        """Apre la finestra della materia"""
        self.subject_window = SubjectWindow(self.subject_data, self.parent_window)
        self.subject_window.show()
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.subject_windows = []  # Tiene traccia delle finestre aperte
        self.setup_ui()
        self.load_subjects()
        
    def setup_ui(self):
        self.setWindowTitle("Synapse - AI Flashcard Generator")
        self.setMinimumSize(1200, 800)
        
        # Applica stili
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
        
        # Contenuto principale
        content = self.create_content()
        main_layout.addWidget(content)
        
    def create_header(self):
        """Crea l'header dell'applicazione"""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(70)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # Logo e titolo
        title_layout = QHBoxLayout()
        
        logo_label = QLabel("🧠")
        logo_label.setStyleSheet("font-size: 28px;")
        title_layout.addWidget(logo_label)
        
        title_label = QLabel("Synapse")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #8B5CF6;
        """)
        title_layout.addWidget(title_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Pulsante impostazioni
        settings_btn = QPushButton("⚙️ Impostazioni")
        settings_btn.setProperty("class", "secondary")
        settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(settings_btn)
        
        return header
    def create_content(self):
        """Crea il contenuto principale con le card delle materie"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(30)
        
        # Intestazione
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("Le tue Materie")
        title.setProperty("class", "title")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Organizza il tuo studio creando materie e generando flashcard con l'AI")
        subtitle.setProperty("class", "body")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        # ScrollArea per le card
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Card "Crea nuova materia"
        create_card = self.create_new_subject_card()
        self.grid_layout.addWidget(create_card, 0, 0)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return content
    
    def create_new_subject_card(self):
        """Crea la card per aggiungere una nuova materia"""
        card = QFrame()
        card.setFixedSize(280, 200)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none; /* NESSUN BORDO */
                border-radius: 16px;
            }
            QFrame:hover {
                /* Hover pulito con solo leggero cambio di sfondo */
                background-color: #F8F8F8;
                border: none;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # Icona
        icon_label = QLabel("➕")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Testo
        text_label = QLabel("Nuova Materia")
        text_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #262626;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
        
        desc_label = QLabel("Crea una nuova cartella di studio")
        desc_label.setStyleSheet("font-size: 13px; color: #737373;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        card.mousePressEvent = lambda e: self.create_subject()
        
        return card
    
    def load_subjects(self):
        """Carica e visualizza tutte le materie"""
        subjects = self.db.get_all_subjects()
        
        # Rimuovi tutte le card eccetto la prima (nuova materia)
        for i in reversed(range(1, self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        # Aggiungi le card delle materie
        for idx, subject in enumerate(subjects):
            card = SubjectCard(subject, self)
            row = (idx + 1) // 3
            col = (idx + 1) % 3
            self.grid_layout.addWidget(card, row, col)
    
    def create_subject(self):
        """Mostra il dialog per creare una nuova materia"""
        dialog = CreateSubjectDialog(self)
        if dialog.exec():
            self.load_subjects()
    
    def show_settings(self):
        """Mostra il dialog delle impostazioni"""
        dialog = SettingsDialog(self)
        dialog.exec()