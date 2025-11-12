from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QTextEdit, QVBoxLayout)

from database.db_manager import DatabaseManager
from ui.styles import (SUBJECT_COLORS, get_caption_text_color,
                       get_secondary_text_color, get_text_color)


class CreateSubjectDialog(QDialog):
    """Dialog per creare una nuova materia"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.selected_color = SUBJECT_COLORS[0]
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Crea Nuova Materia")
        self.setFixedSize(520, 540)
        self.setModal(True)
        
        # Centra la finestra allo schermo
        self.center_on_screen()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Header
        self.create_header(layout)
        
        # Form fields
        self.create_form_fields(layout)
        
        # Color picker
        self.create_color_picker(layout)
        
        layout.addStretch()
        
        # Action buttons
        self.create_action_buttons(layout)
    
    def create_header(self, parent_layout):
        """Crea l'intestazione del dialog"""
        title = QLabel("Crea Nuova Materia")
        title.setStyleSheet(f"""
            font-size: 22px; 
            font-weight: 700; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(title)
        
        subtitle = QLabel("Organizza il tuo studio creando una nuova materia")
        subtitle.setStyleSheet(f"""
            font-size: 13px; 
            color: {get_caption_text_color()};
        """)
        subtitle.setWordWrap(True)
        parent_layout.addWidget(subtitle)
    
    def create_form_fields(self, parent_layout):
        """Crea i campi del form"""
        # Nome materia
        name_label = QLabel("Nome Materia *")
        name_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("es. Matematica, Storia, Biologia...")
        self.name_input.setMinimumHeight(44)
        parent_layout.addWidget(self.name_input)
        
        # Descrizione
        desc_label = QLabel("Descrizione (opzionale)")
        desc_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Aggiungi una breve descrizione...")
        self.desc_input.setFixedHeight(90)
        parent_layout.addWidget(self.desc_input)
    
    def create_color_picker(self, parent_layout):
        """Crea il selettore di colore"""
        color_label = QLabel("Colore")
        color_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(color_label)
        
        # Container per i pulsanti colore
        color_container = QHBoxLayout()
        color_container.setSpacing(12)
        
        self.color_buttons = []
        for color in SUBJECT_COLORS:
            btn = self.create_color_button(color)
            color_container.addWidget(btn)
            self.color_buttons.append(btn)
        
        color_container.addStretch()
        parent_layout.addLayout(color_container)
    
    def create_color_button(self, color):
        """Crea un singolo pulsante colore"""
        btn = QPushButton()
        btn.setFixedSize(52, 52)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("color", color)
        btn.clicked.connect(lambda: self.select_color(color))
        
        # Applica lo stile iniziale
        is_selected = (color == self.selected_color)
        self.update_color_button_style(btn, is_selected)
        
        return btn
    
    def update_color_button_style(self, button, selected):
        """Aggiorna lo stile del pulsante colore"""
        color = button.property("color")
        
        # Se il tema è light usa bordo nero, altrimenti bianco
        border_color = '#171717' if get_text_color() == '#171717' else '#E5E5E5' 
        
        if selected:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 3px solid {border_color};
                    border-radius: 12px;
                }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid transparent;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    border-color: {get_caption_text_color()}50;
                }}
            """)
    
    def select_color(self, color):
        """Gestisce la selezione di un colore"""
        self.selected_color = color
        
        # Aggiorna tutti i pulsanti
        for btn in self.color_buttons:
            is_selected = (btn.property("color") == color)
            self.update_color_button_style(btn, is_selected)
    
    def create_action_buttons(self, parent_layout):
        """Crea i pulsanti di azione"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # Annulla
        cancel_btn = QPushButton("Annulla")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Crea
        create_btn = QPushButton("Crea Materia")
        create_btn.setProperty("class", "primary")
        create_btn.setMinimumHeight(44)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self.create_subject)
        button_layout.addWidget(create_btn)
        
        parent_layout.addLayout(button_layout)
    
    def create_subject(self):
        """Crea la nuova materia"""
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(
                self, 
                "Campo Obbligatorio", 
                "Il nome della materia è obbligatorio"
            )
            return
        
        description = self.desc_input.toPlainText().strip() or None
        
        try:
            self.db.create_subject(name, description, self.selected_color)
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Errore", 
                f"Errore nella creazione della materia:\n{str(e)}"
            )
    
    def center_on_screen(self):
        """Centra la finestra sullo schermo"""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
