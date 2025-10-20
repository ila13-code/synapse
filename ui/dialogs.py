from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QComboBox,
                             QGridLayout, QFrame, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt
from database.db_manager import DatabaseManager
from ui.styles import SUBJECT_COLORS
import os

class CreateSubjectDialog(QDialog):
    """Dialog per creare una nuova materia"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.selected_color = SUBJECT_COLORS[0]
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Crea Nuova Materia")
        self.setFixedSize(500, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Titolo
        title = QLabel("Crea Nuova Materia")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #171717;")
        layout.addWidget(title)
        
        subtitle = QLabel("Organizza il tuo studio creando una nuova materia")
        subtitle.setStyleSheet("font-size: 13px; color: #737373;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        # Nome materia
        name_label = QLabel("Nome Materia *")
        name_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #262626;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("es. Matematica, Storia, Biologia...")
        self.name_input.setMinimumHeight(40)
        layout.addWidget(self.name_input)
        
        # Descrizione
        desc_label = QLabel("Descrizione (opzionale)")
        desc_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #262626;")
        layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Aggiungi una breve descrizione...")
        self.desc_input.setFixedHeight(80)
        layout.addWidget(self.desc_input)
        
        # Selezione colore
        color_label = QLabel("Colore")
        color_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #262626;")
        layout.addWidget(color_label)
        
        color_layout = QHBoxLayout()
        color_layout.setSpacing(10)
        
        self.color_buttons = []
        for color in SUBJECT_COLORS:
            btn = QPushButton()
            btn.setFixedSize(50, 50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("color", color)
            btn.clicked.connect(lambda checked, c=color: self.select_color(c))
            self.update_color_button_style(btn, color == self.selected_color)
            color_layout.addWidget(btn)
            self.color_buttons.append(btn)
        
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        layout.addStretch()
        
        # Pulsanti
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Annulla")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Crea Materia")
        create_btn.setProperty("class", "primary")
        create_btn.setMinimumHeight(40)
        create_btn.clicked.connect(self.create_subject)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
    def update_color_button_style(self, button, selected):
        color = button.property("color")
        if selected:
            button.setStyleSheet(f"""
                background-color: {color};
                border: 3px solid #171717;
                border-radius: 12px;
            """)
        else:
            button.setStyleSheet(f"""
                background-color: {color};
                border: none;
                border-radius: 12px;
            """)
    
    def select_color(self, color):
        self.selected_color = color
        for btn in self.color_buttons:
            self.update_color_button_style(btn, btn.property("color") == color)
    
    def create_subject(self):
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Errore", "Il nome della materia è obbligatorio")
            return
        
        description = self.desc_input.toPlainText().strip() or None
        
        try:
            self.db.create_subject(name, description, self.selected_color)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nella creazione della materia: {e}")


class SettingsDialog(QDialog):
    """Dialog per le impostazioni (API Key)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        self.setWindowTitle("Impostazioni")
        self.setFixedSize(600, 350)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Titolo
        title = QLabel("Impostazioni")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #171717;")
        layout.addWidget(title)
        
        # API Key
        api_label = QLabel("Gemini API Key *")
        api_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #262626;")
        layout.addWidget(api_label)
        
        help_label = QLabel('<a href="https://aistudio.google.com/app/apikey">Ottieni la tua API key qui</a>')
        help_label.setStyleSheet("font-size: 12px; color: #737373;")
        help_label.setOpenExternalLinks(True)
        layout.addWidget(help_label)
        
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("Inserisci la tua Gemini API key...")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setMinimumHeight(40)
        layout.addWidget(self.api_input)
        
        # Mostra/Nascondi password
        show_layout = QHBoxLayout()
        self.show_btn = QPushButton("👁️ Mostra")
        self.show_btn.setProperty("class", "secondary")
        self.show_btn.setFixedWidth(100)
        self.show_btn.clicked.connect(self.toggle_password_visibility)
        show_layout.addWidget(self.show_btn)
        show_layout.addStretch()
        layout.addLayout(show_layout)
        
        layout.addStretch()
        
        # Pulsanti
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Annulla")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Salva")
        save_btn.setProperty("class", "primary")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
    def toggle_password_visibility(self):
        if self.api_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_btn.setText("🔒 Nascondi")
        else:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_btn.setText("👁️ Mostra")
    
    def load_settings(self):
        """Carica le impostazioni salvate"""
        api_key = os.environ.get('GEMINI_API_KEY', '')
        self.api_input.setText(api_key)
    
    def save_settings(self):
        """Salva le impostazioni"""
        api_key = self.api_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "Errore", "L'API key è obbligatoria")
            return
        
        # Salva nell'ambiente
        os.environ['GEMINI_API_KEY'] = api_key
        
        # Salva in un file config locale
        try:
            with open('.env', 'w') as f:
                f.write(f'GEMINI_API_KEY={api_key}\n')
        except Exception as e:
            print(f"Warning: Could not save to .env file: {e}")
        
        QMessageBox.information(self, "Successo", "Impostazioni salvate con successo!")
        self.accept()


class EditFlashcardDialog(QDialog):
    """Dialog per modificare una flashcard"""
    
    def __init__(self, flashcard_data, parent=None):
        super().__init__(parent)
        self.flashcard_data = flashcard_data
        self.db = DatabaseManager()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Modifica Flashcard")
        self.setFixedSize(600, 550)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Titolo
        title = QLabel("Modifica Flashcard")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #171717;")
        layout.addWidget(title)
        
        # Domanda
        front_label = QLabel("Domanda")
        front_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #262626;")
        layout.addWidget(front_label)
        
        self.front_input = QTextEdit()
        self.front_input.setPlainText(self.flashcard_data['front'])
        self.front_input.setFixedHeight(100)
        layout.addWidget(self.front_input)
        
        # Risposta
        back_label = QLabel("Risposta")
        back_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #262626;")
        layout.addWidget(back_label)
        
        self.back_input = QTextEdit()
        self.back_input.setPlainText(self.flashcard_data['back'])
        self.back_input.setFixedHeight(120)
        layout.addWidget(self.back_input)
        
        # Difficoltà
        diff_label = QLabel("Difficoltà")
        diff_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #262626;")
        layout.addWidget(diff_label)
        
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(['easy', 'medium', 'hard'])
        self.diff_combo.setCurrentText(self.flashcard_data.get('difficulty', 'medium'))
        self.diff_combo.setMinimumHeight(40)
        layout.addWidget(self.diff_combo)
        
        layout.addStretch()
        
        # Pulsanti
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Annulla")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Salva Modifiche")
        save_btn.setProperty("class", "primary")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_changes)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def save_changes(self):
        front = self.front_input.toPlainText().strip()
        back = self.back_input.toPlainText().strip()
        difficulty = self.diff_combo.currentText()
        
        if not front or not back:
            QMessageBox.warning(self, "Errore", "Domanda e risposta non possono essere vuote")
            return
        
        try:
            self.db.update_flashcard(
                self.flashcard_data['id'],
                front,
                back,
                difficulty
            )
            QMessageBox.information(self, "Successo", "Flashcard aggiornata con successo!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'aggiornamento: {e}")