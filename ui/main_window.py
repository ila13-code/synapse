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
        layout.setSpacing(8)

        icon_label = QLabel("📚")
        icon_label.setStyleSheet(f"font-size: 28px; color: {accent_color};")
        layout.addWidget(icon_label)
        

        layout.addStretch()
        

        name_label = QLabel(self.subject_data['name'])
        name_label.setWordWrap(True)
        name_label.setProperty("class", "card_text") 
        name_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #171717;")
        layout.addWidget(name_label)
        

        if self.subject_data.get('description'):
            desc_label = QLabel(self.subject_data['description'])
            desc_label.setWordWrap(True)
            desc_label.setProperty("class", "card_text") 
            desc_label.setStyleSheet("font-size: 13px; color: #525252;")
            layout.addWidget(desc_label)
        
        if not self.subject_data.get('description'):
             layout.addSpacing(18) 
        
        date_label = QLabel(f"Creata il {self.subject_data['created_at'][:10]}")
        date_label.setProperty("class", "card_text")
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
        self.subject_windows = [] 
        self.setup_ui()
        self.load_subjects()
        
    def setup_ui(self):
        self.setWindowTitle("Synapse - AI Flashcard Generator")
        self.setMinimumSize(1200, 800)
        
        self.setStyleSheet(MAIN_STYLE)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        

        header = self.create_header()
        main_layout.addWidget(header)
        

        content = self.create_content()
        main_layout.addWidget(content)
        
    def create_header(self):
        """Crea l'header dell'applicazione"""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(70)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        
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
        
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("Le tue Materie")
        title.setProperty("class", "title")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Organizza il tuo studio creando materie e generando flashcard con l'AI")
        subtitle.setProperty("class", "body")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)


        scroll_content = QWidget()
        
        centering_layout = QHBoxLayout(scroll_content)
        centering_layout.setContentsMargins(0, 0, 0, 0)
        
        grid_wrapper = QWidget()
        self.grid_layout = QGridLayout(grid_wrapper)
        self.grid_layout.setSpacing(24)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft) 
        
        centering_layout.addWidget(grid_wrapper, alignment=Qt.AlignmentFlag.AlignCenter) # Centra orizzontalmente

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
        

        icon_label = QLabel("➕")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
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
        """Carica e visualizza tutte le materie, mantenendo la card 'Nuova Materia' in posizione (0,0)"""
        subjects = self.db.get_all_subjects()

        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            position = self.grid_layout.getItemPosition(i)
        
            if position == (0, 0, 1, 1):
                continue

            if item:
                self.grid_layout.removeItem(item)
                if item.widget():
                    item.widget().deleteLater()
                elif item.spacerItem():
                    pass
        COLUMNS = 4
        
        for idx, subject in enumerate(subjects):
            card = SubjectCard(subject, self)

            item_index = idx + 1
            row = item_index // COLUMNS
            col = item_index % COLUMNS
            
            self.grid_layout.addWidget(card, row, col)
        
        self.grid_layout.setColumnStretch(COLUMNS, 1)

        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
    
    def create_subject(self):
        """Mostra il dialog per creare una nuova materia"""
        dialog = CreateSubjectDialog(self)
        if dialog.exec():
            self.load_subjects()
    
    def show_settings(self):
        """Mostra il dialog delle impostazioni"""
        dialog = SettingsDialog(self)
        dialog.exec()