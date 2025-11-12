import os

from PyQt6.QtCore import (QEasingCurve, QFileSystemWatcher, QPointF,
                          QPropertyAnimation, Qt, QTimer, pyqtProperty,
                          pyqtSignal)
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QHBoxLayout,
                             QLabel, QLineEdit, QMessageBox, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget)

from database.db_manager import DatabaseManager
from ui.icons import IconProvider
# AGGIORNATO: Importa tutte le funzioni di stile necessarie
from ui.styles import (SUBJECT_COLORS, get_caption_text_color,
                       get_card_background, get_icon_color,
                       get_secondary_text_color, get_text_color)


class ToggleSwitch(QWidget):
    """Widget toggle switch iOS-style con animazione"""
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._circle_position = 0.0
        self.setFixedSize(50, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Animazione per il movimento della pallina
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)
    
    @pyqtProperty(float)
    def circle_position(self):
        return self._circle_position
    
    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()
    
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(1.0 if checked else 0.0)
            self.animation.start()
    
    def isChecked(self):
        return self._checked
    
    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.animation.setStartValue(self._circle_position)
        self.animation.setEndValue(1.0 if self._checked else 0.0)
        self.animation.start()
        self.toggled.emit(self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background track
        track_color = QColor('#8B5CF6') if self._checked else QColor('#D1D5DB')
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 50, 26, 13, 13)
        
        # Circle (pallina)
        circle_x = 3 + (50 - 26) * self._circle_position
        painter.setBrush(QBrush(QColor('#FFFFFF')))
        painter.drawEllipse(int(circle_x), 3, 20, 20)


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
        # USA TEMA
        title.setStyleSheet(f"""
            font-size: 22px; 
            font-weight: 700; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(title)
        
        subtitle = QLabel("Organizza il tuo studio creando una nuova materia")
        # USA TEMA
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
        # USA TEMA
        name_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("es. Matematica, Storia, Biologia...")
        self.name_input.setMinimumHeight(44)
        # RIMOSSO STILE HARDCODATO, usa styles.py
        parent_layout.addWidget(self.name_input)
        
        # Descrizione
        desc_label = QLabel("Descrizione (opzionale)")
        # USA TEMA
        desc_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Aggiungi una breve descrizione...")
        self.desc_input.setFixedHeight(90)
        # RIMOSSO STILE HARDCODATO, usa styles.py
        parent_layout.addWidget(self.desc_input)
    
    def create_color_picker(self, parent_layout):
        """Crea il selettore di colore"""
        color_label = QLabel("Colore")
        # USA TEMA
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
        
        # USA TEMA
        # Se il tema è light (get_text_color() == #171717) usa bordo nero, altrimenti bianco
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


class SettingsDialog(QDialog):
    """Dialog per le impostazioni (API Key)"""
    
    # Segnale per notificare il cambio tema alla MainWindow
    theme_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        # Flag per evitare loop di aggiornamenti (deve essere inizializzato prima di connettere i segnali)
        self.updating_api_key = False
        self.setup_ui()
        self.load_settings()
        
        # Watcher per il file .env
        self.env_watcher = QFileSystemWatcher()
        env_path = os.path.abspath('.env')
        if os.path.exists(env_path):
            self.env_watcher.addPath(env_path)
        self.env_watcher.fileChanged.connect(self.on_env_file_changed)
        
        # Flag per evitare loop di aggiornamenti
        self.updating_api_key = False
    
    def setup_ui(self):
        self.setWindowTitle("Impostazioni")
        self.setFixedSize(600, 400)  # Aumentata l'altezza per contenere i pulsanti cestino
        self.setModal(True)
        
        # Applica il tema al dialog
        from ui.styles import get_theme_style
        self.setStyleSheet(get_theme_style())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Header rimosso
        
        # Theme section
        self.create_theme_section(layout)
        
        # API Key section
        self.create_api_key_section(layout)
        
        layout.addStretch()
        
        # Nessun pulsante di azione (rimossi Annulla e Salva)
    
    def create_header(self, parent_layout):
        """Crea l'intestazione del dialog"""
        header_layout = QHBoxLayout()
        
        # Icona - Usa colore primario hardcodato
        primary_color = '#8B5CF6'
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, 'settings', 32, primary_color)
        header_layout.addWidget(icon_label)
        
        # Titoli
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Impostazioni")
        # USA TEMA
        title.setStyleSheet(f"""
            font-size: 22px; 
            font-weight: 700; 
            color: {get_text_color()};
        """)
        text_layout.addWidget(title)
        
        header_layout.addLayout(text_layout)
        parent_layout.addLayout(header_layout)
    
    
    def create_theme_section(self, parent_layout):
        """Crea la sezione tema (disabilitato)"""
        # Sezione tema rimossa come richiesto
        pass
    
    def create_api_key_section(self, parent_layout):
        """Crea la sezione API Key"""
        # Google Gemini API Key
        api_label = QLabel("Google Gemini API Key *")
        api_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(api_label)
        
        link_label = QLabel(
            f'<a href="https://makersuite.google.com/app/apikey" '
            f'style="color: #8B5CF6; text-decoration: underline;">'
            f'Ottieni la tua API key</a>'
        )
        link_label.setOpenExternalLinks(True)
        link_label.setStyleSheet(f"""
            font-size: 13px;
            color: {get_caption_text_color()};
            padding: 4px 0;
        """)
        parent_layout.addWidget(link_label)
        
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setPlaceholderText("Inserisci la tua API key...")
        self.api_input.setMinimumHeight(44)
        self.api_input.textChanged.connect(self.on_api_key_changed)
        input_layout.addWidget(self.api_input)
        
        # Pulsante mostra/nascondi
        self.show_btn = QPushButton()
        # USA TEMA per l'icona
        self.show_btn.setIcon(IconProvider.get_icon('eye', 16, get_icon_color()))
        self.show_btn.setProperty("class", "secondary")
        self.show_btn.setFixedWidth(100)
        self.show_btn.setMinimumHeight(44)
        self.show_btn.clicked.connect(self.toggle_api_visibility)
        input_layout.addWidget(self.show_btn)
        
        # Pulsante cestino per eliminare API key
        self.delete_gemini_btn = QPushButton()
        self.delete_gemini_btn.setIcon(IconProvider.get_icon('trash', 16, '#FFFFFF'))
        self.delete_gemini_btn.setFixedSize(44, 44)
        self.delete_gemini_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        self.delete_gemini_btn.clicked.connect(self.delete_gemini_api_key)
        input_layout.addWidget(self.delete_gemini_btn)
        
        parent_layout.addLayout(input_layout)
        
        # Spazio tra le due sezioni
        parent_layout.addSpacing(20)
        
        # Tavily API Key
        tavily_label = QLabel("Tavily API Key (opzionale)")
        tavily_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(tavily_label)
        
        tavily_link_label = QLabel(
            f'<a href="https://tavily.com/" '
            f'style="color: #8B5CF6; text-decoration: underline;">'
            f'Ottieni la tua API key</a> - per ricerca web avanzata'
        )
        tavily_link_label.setOpenExternalLinks(True)
        tavily_link_label.setStyleSheet(f"""
            font-size: 13px;
            color: {get_caption_text_color()};
            padding: 4px 0;
        """)
        parent_layout.addWidget(tavily_link_label)
        
        tavily_input_layout = QHBoxLayout()
        tavily_input_layout.setSpacing(8)
        
        self.tavily_api_input = QLineEdit()
        self.tavily_api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.tavily_api_input.setPlaceholderText("Inserisci la tua Tavily API key...")
        self.tavily_api_input.setMinimumHeight(44)
        self.tavily_api_input.textChanged.connect(self.on_tavily_api_key_changed)
        tavily_input_layout.addWidget(self.tavily_api_input)
        
        # Pulsante mostra/nascondi per Tavily
        self.show_tavily_btn = QPushButton()
        self.show_tavily_btn.setIcon(IconProvider.get_icon('eye', 16, get_icon_color()))
        self.show_tavily_btn.setProperty("class", "secondary")
        self.show_tavily_btn.setFixedWidth(100)
        self.show_tavily_btn.setMinimumHeight(44)
        self.show_tavily_btn.clicked.connect(self.toggle_tavily_api_visibility)
        tavily_input_layout.addWidget(self.show_tavily_btn)
        
        # Pulsante cestino per eliminare Tavily API key
        self.delete_tavily_btn = QPushButton()
        self.delete_tavily_btn.setIcon(IconProvider.get_icon('trash', 16, '#FFFFFF'))
        self.delete_tavily_btn.setFixedSize(44, 44)
        self.delete_tavily_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        self.delete_tavily_btn.clicked.connect(self.delete_tavily_api_key)
        tavily_input_layout.addWidget(self.delete_tavily_btn)
        
        parent_layout.addLayout(tavily_input_layout)
        
        # Nota informativa rimossa
    
    def toggle_api_visibility(self):
        """Toggle della visibilità dell'API key"""
        # USA TEMA per l'icona
        icon_color = get_icon_color()

        if self.api_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_btn.setIcon(IconProvider.get_icon('eye-slash', 16, icon_color))
        else:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_btn.setIcon(IconProvider.get_icon('eye', 16, icon_color))
    
    def toggle_tavily_api_visibility(self):
        """Toggle della visibilità dell'API key Tavily"""
        icon_color = get_icon_color()

        if self.tavily_api_input.echoMode() == QLineEdit.EchoMode.Password:
            self.tavily_api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_tavily_btn.setIcon(IconProvider.get_icon('eye-slash', 16, icon_color))
        else:
            self.tavily_api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_tavily_btn.setIcon(IconProvider.get_icon('eye', 16, icon_color))
    
    def on_theme_toggle(self, checked):
        """Gestisce il cambio immediato del tema quando viene cliccato il toggle (disabilitato)"""
        # Funzione disabilitata - tema dark mode rimosso
        pass
    
    def on_api_key_changed(self, text):
        """Salva automaticamente l'API key nel file .env quando cambia il contenuto"""
        # Evita loop di aggiornamenti
        if self.updating_api_key:
            return
            
        api_key = text.strip()
        
        # Aggiorna l'ambiente
        if api_key:
            os.environ['GEMINI_API_KEY'] = api_key
        elif 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
        
        # Salva nel file .env
        self._save_env_variable('GEMINI_API_KEY', api_key)
    
    def on_tavily_api_key_changed(self, text):
        """Salva automaticamente la Tavily API key nel file .env quando cambia il contenuto"""
        if self.updating_api_key:
            return
            
        api_key = text.strip()
        
        # Aggiorna l'ambiente
        if api_key:
            os.environ['TAVILY_API_KEY'] = api_key
        elif 'TAVILY_API_KEY' in os.environ:
            del os.environ['TAVILY_API_KEY']
        
        # Salva nel file .env
        self._save_env_variable('TAVILY_API_KEY', api_key)
    
    def _save_env_variable(self, key: str, value: str):
        """Salva una variabile d'ambiente nel file .env"""
        try:
            env_path = '.env'
            
            # Leggi tutte le altre variabili esistenti
            existing_vars = {}
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            var_key, var_value = line.split('=', 1)
                            var_key = var_key.strip()
                            if var_key != key:
                                existing_vars[var_key] = var_value.strip()
            
            # Scrivi tutte le variabili
            with open(env_path, 'w', encoding='utf-8') as f:
                # Scrivi la variabile che stiamo salvando (se non vuota)
                if value:
                    f.write(f'{key}={value}\n')
                # Scrivi tutte le altre variabili
                for k, v in existing_vars.items():
                    f.write(f'{k}={v}\n')
        except Exception as e:
            print(f"Errore durante il salvataggio di {key}: {e}")
    
    def on_env_file_changed(self, path):
        """Aggiorna la textbox quando il file .env viene modificato esternamente"""
        # Riaggiunge il file al watcher (necessario su alcuni sistemi)
        if not self.env_watcher.files():
            self.env_watcher.addPath(path)
        
        # Leggi il nuovo valore dal file
        try:
            self.updating_api_key = True
            api_key = ''
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GEMINI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
            
            # Aggiorna la textbox solo se il valore è cambiato
            if self.api_input.text() != api_key:
                self.api_input.setText(api_key)
                if api_key:
                    os.environ['GEMINI_API_KEY'] = api_key
        except Exception as e:
            print(f"Errore durante la lettura del file .env: {e}")
        finally:
            self.updating_api_key = False
    
    def delete_gemini_api_key(self):
        """Elimina la Gemini API key"""
        reply = QMessageBox.question(
            self,
            "Elimina API Key",
            "Sei sicuro di voler eliminare la Gemini API key?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.api_input.clear()
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']
            self._save_env_variable('GEMINI_API_KEY', '')
    
    def delete_tavily_api_key(self):
        """Elimina la Tavily API key"""
        reply = QMessageBox.question(
            self,
            "Elimina API Key",
            "Sei sicuro di voler eliminare la Tavily API key?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.tavily_api_input.clear()
            if 'TAVILY_API_KEY' in os.environ:
                del os.environ['TAVILY_API_KEY']
            self._save_env_variable('TAVILY_API_KEY', '')
    
    def load_settings(self):
        """Carica le impostazioni salvate"""
        # Sezione tema dark mode rimossa
        
        # Carica Gemini API key
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
        
        # Carica Tavily API key
        tavily_key = os.environ.get('TAVILY_API_KEY', '')
        
        if not tavily_key:
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if line.startswith('TAVILY_API_KEY='):
                            tavily_key = line.split('=', 1)[1].strip()
                            break
            except FileNotFoundError:
                pass
        
        if tavily_key:
            self.tavily_api_input.setText(tavily_key)
    
    # Metodo save_settings rimosso - il salvataggio è automatico


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
        
        # Icona - Usa colore primario hardcodato
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, 'edit', 28, '#8B5CF6')
        header_layout.addWidget(icon_label)
        
        # Titoli
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Modifica Flashcard")
        # USA TEMA
        title.setStyleSheet(f"""
            font-size: 22px; 
            font-weight: 700; 
            color: {get_text_color()};
        """)
        text_layout.addWidget(title)
        
        subtitle = QLabel("Modifica il contenuto e la difficoltà della flashcard")
        # USA TEMA
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
        # USA TEMA
        front_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(front_label)
        
        self.front_input = QTextEdit()
        self.front_input.setPlainText(self.flashcard_data['front'])
        self.front_input.setFixedHeight(120)
        # RIMOSSO STILE HARDCODATO, usa styles.py
        parent_layout.addWidget(self.front_input)
        
        # Risposta (retro)
        back_label = QLabel("Risposta (Retro)")
        # USA TEMA
        back_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_secondary_text_color()};
        """)
        parent_layout.addWidget(back_label)
        
        self.back_input = QTextEdit()
        self.back_input.setPlainText(self.flashcard_data['back'])
        self.back_input.setFixedHeight(140)
        # RIMOSSO STILE HARDCODATO, usa styles.py
        parent_layout.addWidget(self.back_input)
        
        # Difficoltà
        diff_label = QLabel("Difficoltà")
        # USA TEMA
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
        # RIMOSSO STILE HARDCODATO, usa styles.py
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