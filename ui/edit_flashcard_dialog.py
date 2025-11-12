from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel,
                             QMessageBox, QPushButton, QTextEdit, QVBoxLayout)

from database.db_manager import DatabaseManager
from ui.icons import IconProvider
from ui.styles import (get_caption_text_color, get_secondary_text_color,
                       get_text_color)


class EditFlashcardDialog(QDialog):
    """Dialog per modificare una flashcard"""
    
    def __init__(self, flashcard_data, parent=None):
        super().__init__(parent)
        self.flashcard_data = flashcard_data
        self.db = DatabaseManager()
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Modifica Flashcard")
        self.setFixedSize(600, 600)
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
        
        layout.addStretch()
        
        # Action buttons
        self.create_action_buttons(layout)
    
    def create_header(self, parent_layout):
        """Crea l'intestazione del dialog"""
        header_layout = QHBoxLayout()
        
        # Icona
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, 'edit', 28, '#8B5CF6')
        header_layout.addWidget(icon_label)
        
        # Titoli
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Modifica Flashcard")
        title.setStyleSheet(f"""
            font-size: 22px; 
            font-weight: 700; 
            color: {get_text_color()};
        """)
        text_layout.addWidget(title)
        
        subtitle = QLabel("Modifica il contenuto e la difficoltà della flashcard")
        subtitle.setStyleSheet(f"""
            font-size: 13px; 
            color: {get_caption_text_color()};
        """)
        text_layout.addWidget(subtitle)
        
        header_layout.addLayout(text_layout)
        parent_layout.addLayout(header_layout)
    
    def create_form_fields(self, parent_layout):
        """Crea i campi del form"""
        # Domanda (fronte)
        front_label = QLabel("Domanda (Fronte)")
        front_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(front_label)
        
        self.front_input = QTextEdit()
        self.front_input.setPlainText(self.flashcard_data['front'])
        self.front_input.setFixedHeight(120)
        parent_layout.addWidget(self.front_input)
        
        # Risposta (retro)
        back_label = QLabel("Risposta (Retro)")
        back_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(back_label)
        
        self.back_input = QTextEdit()
        self.back_input.setPlainText(self.flashcard_data['back'])
        self.back_input.setFixedHeight(140)
        parent_layout.addWidget(self.back_input)
        
        # Difficoltà
        diff_label = QLabel("Difficoltà")
        diff_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(diff_label)
        
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(['facile', 'medio', 'difficile'])
        
        # Mappa i valori dal database
        difficulty_map = {
            'easy': 'facile',
            'medium': 'medio',
            'hard': 'difficile',
            'facile': 'facile',
            'medio': 'medio',
            'difficile': 'difficile'
        }
        
        current_difficulty = self.flashcard_data.get('difficulty', 'medio')
        mapped_difficulty = difficulty_map.get(current_difficulty, 'medio')
        self.diff_combo.setCurrentText(mapped_difficulty)
        
        self.diff_combo.setMinimumHeight(44)
        parent_layout.addWidget(self.diff_combo)
    
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
        
        # Salva con icona
        save_btn = QPushButton(" Salva Modifiche")
        save_btn.setIcon(IconProvider.get_icon('save', 18, '#FFFFFF'))
        save_btn.setProperty("class", "primary")
        save_btn.setMinimumHeight(44)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_changes)
        button_layout.addWidget(save_btn)
        
        parent_layout.addLayout(button_layout)
    
    def save_changes(self):
        """Salva le modifiche alla flashcard"""
        front = self.front_input.toPlainText().strip()
        back = self.back_input.toPlainText().strip()
        
        if not front or not back:
            QMessageBox.warning(
                self, 
                "Campi Obbligatori", 
                "Domanda e risposta non possono essere vuote"
            )
            return
        
        # Mappa la difficoltà in italiano -> inglese per il database
        difficulty_reverse_map = {
            'facile': 'easy',
            'medio': 'medium',
            'difficile': 'hard'
        }
        
        difficulty_it = self.diff_combo.currentText()
        difficulty = difficulty_reverse_map.get(difficulty_it, 'medium')
        
        try:
            self.db.update_flashcard(
                self.flashcard_data['id'],
                front,
                back,
                difficulty
            )
            
            QMessageBox.information(
                self, 
                "Successo", 
                "Flashcard aggiornata con successo!"
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Errore", 
                f"Errore nell'aggiornamento della flashcard:\n{str(e)}"
            )
    
    def center_on_screen(self):
        """Centra la finestra sullo schermo"""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
