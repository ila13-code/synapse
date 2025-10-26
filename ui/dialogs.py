from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QComboBox,
                             QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.db_manager import DatabaseManager
from ui.styles import SUBJECT_COLORS
from ui.icons import IconProvider
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
        self.setFixedSize(520, 540)
        self.setModal(True)
        
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
        title.setStyleSheet("""
            font-size: 22px; 
            font-weight: 700; 
            color: #171717;
        """)
        parent_layout.addWidget(title)
        
        subtitle = QLabel("Organizza il tuo studio creando una nuova materia")
        subtitle.setStyleSheet("""
            font-size: 13px; 
            color: #737373;
        """)
        subtitle.setWordWrap(True)
        parent_layout.addWidget(subtitle)
    
    def create_form_fields(self, parent_layout):
        """Crea i campi del form"""
        # Nome materia
        name_label = QLabel("Nome Materia *")
        name_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #262626;
        """)
        parent_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("es. Matematica, Storia, Biologia...")
        self.name_input.setMinimumHeight(44)
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 0 12px;
                border: 2px solid #E5E5E5;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #8B5CF6;
            }
        """)
        parent_layout.addWidget(self.name_input)
        
        # Descrizione
        desc_label = QLabel("Descrizione (opzionale)")
        desc_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #262626;
        """)
        parent_layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Aggiungi una breve descrizione...")
        self.desc_input.setFixedHeight(90)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                padding: 12px;
                border: 2px solid #E5E5E5;
                border-radius: 8px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #8B5CF6;
            }
        """)
        parent_layout.addWidget(self.desc_input)
    
    def create_color_picker(self, parent_layout):
        """Crea il selettore di colore"""
        color_label = QLabel("Colore")
        color_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #262626;
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
        
        if selected:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 3px solid #171717;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    transform: scale(1.05);
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
                    border-color: #D4D4D4;
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


class SettingsDialog(QDialog):
    """Dialog per le impostazioni (API Key)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        self.setWindowTitle("Impostazioni")
        self.setFixedSize(600, 520)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Header
        self.create_header(layout)
        
        # API Key section
        self.create_api_key_section(layout)
        
        layout.addStretch()
        
        # Action buttons
        self.create_action_buttons(layout)
    
    def create_header(self, parent_layout):
        """Crea l'intestazione del dialog"""
        header_layout = QHBoxLayout()
        
        # Icona
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, 'settings', 32, '#8B5CF6')
        header_layout.addWidget(icon_label)
        
        # Titoli
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Impostazioni")
        title.setStyleSheet("""
            font-size: 22px; 
            font-weight: 700; 
            color: #171717;
        """)
        text_layout.addWidget(title)
        
        subtitle = QLabel("Configura l'API Key di Google Gemini per abilitare le funzionalità AI")
        subtitle.setStyleSheet("""
            font-size: 13px; 
            color: #737373;
        """)
        subtitle.setWordWrap(True)
        text_layout.addWidget(subtitle)
        
        header_layout.addLayout(text_layout)
        parent_layout.addLayout(header_layout)
    
    def create_api_key_section(self, parent_layout):
        """Crea la sezione API Key"""
        # Label
        api_label = QLabel("Google Gemini API Key *")
        api_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #262626;
        """)
        parent_layout.addWidget(api_label)
        
        # Link per ottenere API key
        link_label = QLabel(
            '<a href="https://makersuite.google.com/app/apikey" '
            'style="color: #8B5CF6; text-decoration: none;">'
            'Ottieni la tua API key</a>'
        )
        link_label.setOpenExternalLinks(True)
        link_label.setStyleSheet("""
            font-size: 13px;
            padding: 4px 0;
        """)
        parent_layout.addWidget(link_label)
        
        # Input container con pulsante mostra/nascondi
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setPlaceholderText("Inserisci la tua API key...")
        self.api_input.setMinimumHeight(44)
        self.api_input.setStyleSheet("""
            QLineEdit {
                padding: 0 12px;
                border: 2px solid #E5E5E5;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #8B5CF6;
            }
        """)
        input_layout.addWidget(self.api_input)
        
        # Pulsante mostra/nascondi
        self.show_btn = QPushButton(" Mostra")
        self.show_btn.setIcon(IconProvider.get_icon('key', 16, '#262626'))
        self.show_btn.setProperty("class", "secondary")
        self.show_btn.setFixedWidth(100)
        self.show_btn.setMinimumHeight(44)
        self.show_btn.clicked.connect(self.toggle_api_visibility)
        input_layout.addWidget(self.show_btn)
        
        parent_layout.addLayout(input_layout)
        
        # Nota informativa
        info_label = QLabel(
            "<b>Nota sulla sicurezza:</b> La tua API key viene salvata localmente "
            "sul tuo computer e non viene mai inviata a server esterni. "
            "Viene utilizzata solo per comunicare direttamente con Google Gemini."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #F3F4F6;
                border-left: 4px solid #8B5CF6;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 12px;
                color: #525252;
            }
        """)
        parent_layout.addWidget(info_label)
    
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
        save_btn = QPushButton(" Salva Impostazioni")
        save_btn.setIcon(IconProvider.get_icon('save', 18, '#FFFFFF'))
        save_btn.setProperty("class", "primary")
        save_btn.setMinimumHeight(44)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        parent_layout.addLayout(button_layout)
    
    def toggle_api_visibility(self):
        """Toggle della visibilità dell'API key"""
        if self.api_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_btn.setText(" Nascondi")
        else:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_btn.setText(" Mostra")
    
    def load_settings(self):
        """Carica le impostazioni salvate"""
        # Cerca prima nell'ambiente
        api_key = os.environ.get('GEMINI_API_KEY', '')
        
        # Se non c'è, prova a leggere da .env
        if not api_key:
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if line.startswith('GEMINI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            break
            except FileNotFoundError:
                pass
        
        if api_key:
            self.api_input.setText(api_key)
    
    def save_settings(self):
        """Salva le impostazioni"""
        api_key = self.api_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(
                self, 
                "Campo Obbligatorio", 
                "L'API key di Google Gemini è obbligatoria per utilizzare le funzionalità AI"
            )
            return
        
        # Validazione base dell'API key (lunghezza minima)
        if len(api_key) < 20:
            QMessageBox.warning(
                self, 
                "API Key Non Valida", 
                "L'API key inserita sembra non essere valida. "
                "Assicurati di aver copiato correttamente l'intera chiave da Google AI Studio."
            )
            return
        
        # Salva nell'ambiente
        os.environ['GEMINI_API_KEY'] = api_key
        
        # Salva in un file .env locale
        try:
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(f'GEMINI_API_KEY={api_key}\n')
        except Exception as e:
            QMessageBox.warning(
                self,
                "Avviso",
                f"Impossibile salvare nel file .env: {e}\n\n"
                "L'API key è stata salvata solo per questa sessione."
            )
        
        QMessageBox.information(
            self, 
            "Successo", 
            "Impostazioni salvate con successo!\n\n"
            "Ora puoi utilizzare tutte le funzioni AI."
        )
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
        self.setFixedSize(600, 600)
        self.setModal(True)
        
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
        title.setStyleSheet("""
            font-size: 22px; 
            font-weight: 700; 
            color: #171717;
        """)
        text_layout.addWidget(title)
        
        subtitle = QLabel("Modifica il contenuto e la difficoltà della flashcard")
        subtitle.setStyleSheet("""
            font-size: 13px; 
            color: #737373;
        """)
        text_layout.addWidget(subtitle)
        
        header_layout.addLayout(text_layout)
        parent_layout.addLayout(header_layout)
    
    def create_form_fields(self, parent_layout):
        """Crea i campi del form"""
        # Domanda (fronte)
        front_label = QLabel("Domanda (Fronte)")
        front_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #262626;
        """)
        parent_layout.addWidget(front_label)
        
        self.front_input = QTextEdit()
        self.front_input.setPlainText(self.flashcard_data['front'])
        self.front_input.setFixedHeight(120)
        self.front_input.setStyleSheet("""
            QTextEdit {
                padding: 12px;
                border: 2px solid #E5E5E5;
                border-radius: 8px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #8B5CF6;
            }
        """)
        parent_layout.addWidget(self.front_input)
        
        # Risposta (retro)
        back_label = QLabel("Risposta (Retro)")
        back_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #262626;
        """)
        parent_layout.addWidget(back_label)
        
        self.back_input = QTextEdit()
        self.back_input.setPlainText(self.flashcard_data['back'])
        self.back_input.setFixedHeight(140)
        self.back_input.setStyleSheet("""
            QTextEdit {
                padding: 12px;
                border: 2px solid #E5E5E5;
                border-radius: 8px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #8B5CF6;
            }
        """)
        parent_layout.addWidget(self.back_input)
        
        # Difficoltà
        diff_label = QLabel("Difficoltà")
        diff_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: 600; 
            color: #262626;
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
        self.diff_combo.setStyleSheet("""
            QComboBox {
                padding: 0 12px;
                border: 2px solid #E5E5E5;
                border-radius: 8px;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #8B5CF6;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #737373;
                margin-right: 10px;
            }
        """)
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