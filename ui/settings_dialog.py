import os

from PyQt6.QtCore import QFileSystemWatcher, Qt, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget)

from config.env_loader import get_env_bool
from database.db_manager import DatabaseManager
from ui.icons import IconProvider
from ui.styles import (get_caption_text_color, get_card_background,
                       get_icon_color, get_secondary_text_color,
                       get_text_color)
from ui.toggle_switch import ToggleSwitch


class SettingsDialog(QDialog):
    """Dialog per le impostazioni (API Key)"""
    
    # Segnale per notificare il cambio tema alla MainWindow
    theme_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        # Flag per evitare loop di aggiornamenti
        self.updating_api_key = False
        self.power_user_mode = False
        self.setup_ui()
        self.load_settings()
        
        # Watcher per il file .env
        self.env_watcher = QFileSystemWatcher()
        env_path = os.path.abspath('.env')
        if os.path.exists(env_path):
            self.env_watcher.addPath(env_path)
        self.env_watcher.fileChanged.connect(self.on_env_file_changed)
    
    def setup_ui(self):
        self.setWindowTitle("Impostazioni")
        self.setFixedWidth(900)  # Larghezza aumentata
        self.setModal(True)
        
        # Applica il tema al dialog
        from ui.styles import get_theme_style
        self.setStyleSheet(get_theme_style())
        
        # Scroll area per contenere tutte le impostazioni
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Header con toggle modalità
        self.create_mode_toggle(layout)
        
        # Grid layout a due colonne per le sezioni
        grid = QGridLayout()
        grid.setSpacing(20)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        
        # Colonna sinistra: API Keys
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        self.create_api_key_section(left_layout)
        grid.addWidget(left_col, 0, 0)
        
        # Colonna destra: Power User (inizialmente nascosta)
        self.power_user_widget = QWidget()
        self.power_user_layout = QVBoxLayout(self.power_user_widget)
        self.power_user_layout.setContentsMargins(0, 0, 0, 0)
        self.power_user_layout.setSpacing(20)
        self.create_power_user_section(self.power_user_layout)
        self.power_user_widget.setVisible(False)
        grid.addWidget(self.power_user_widget, 0, 1)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def create_mode_toggle(self, parent_layout):
        """Crea il toggle per modalità Base/Power User"""
        mode_frame = QFrame()
        mode_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {get_card_background()};
                border: 2px solid #8B5CF6;
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setSpacing(12)
        
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, 'settings', 24, '#8B5CF6')
        mode_layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Impostazioni")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {get_text_color()};
        """)
        text_layout.addWidget(title)
        
        subtitle = QLabel("Modalità Base")
        subtitle.setStyleSheet(f"""
            font-size: 13px;
            color: {get_caption_text_color()};
        """)
        text_layout.addWidget(subtitle)
        self.mode_subtitle = subtitle
        
        mode_layout.addLayout(text_layout)
        mode_layout.addStretch()
        
        # Toggle per modalità Power User
        mode_label = QLabel("Power User")
        mode_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {get_secondary_text_color()};
        """)
        mode_layout.addWidget(mode_label)
        
        self.mode_toggle = ToggleSwitch()
        self.mode_toggle.toggled.connect(self.toggle_power_user_mode)
        mode_layout.addWidget(self.mode_toggle)
        
        parent_layout.addWidget(mode_frame)
    
    def toggle_power_user_mode(self, checked):
        """Attiva/disattiva la modalità Power User"""
        self.power_user_mode = checked
        self.power_user_widget.setVisible(checked)
        
        # Aggiorna il sottotitolo
        if checked:
            self.mode_subtitle.setText("Modalità Power User - Impostazioni Avanzate")
        else:
            self.mode_subtitle.setText("Modalità Base")
    
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
    
    def create_power_user_section(self, parent_layout):
        """Crea la sezione con parametri avanzati per Power User"""
        # Titolo sezione
        power_title = QLabel("⚡ Impostazioni Avanzate")
        power_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: #8B5CF6;
            padding: 8px 0;
        """)
        parent_layout.addWidget(power_title)
        
        # USE_RAG
        rag_label = QLabel("Abilita RAG (Retrieval-Augmented Generation)")
        rag_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(rag_label)
        
        rag_desc = QLabel("Migliora la generazione usando la ricerca semantica sui documenti")
        rag_desc.setStyleSheet(f"""
            font-size: 12px;
            color: {get_caption_text_color()};
            padding-bottom: 8px;
        """)
        parent_layout.addWidget(rag_desc)
        
        rag_layout = QHBoxLayout()
        self.rag_toggle = ToggleSwitch()
        self.rag_toggle.toggled.connect(lambda checked: self._save_env_variable('USE_RAG', 'true' if checked else 'false'))
        rag_layout.addWidget(self.rag_toggle)
        rag_layout.addStretch()
        parent_layout.addLayout(rag_layout)
        
        parent_layout.addSpacing(12)
        
        # USE_REFLECTION
        reflection_label = QLabel("Abilita Reflection")
        reflection_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(reflection_label)
        
        reflection_desc = QLabel("Usa un processo iterativo di auto-critica per migliorare la qualità")
        reflection_desc.setStyleSheet(f"""
            font-size: 12px;
            color: {get_caption_text_color()};
            padding-bottom: 8px;
        """)
        parent_layout.addWidget(reflection_desc)
        
        reflection_layout = QHBoxLayout()
        self.reflection_toggle = ToggleSwitch()
        self.reflection_toggle.toggled.connect(lambda checked: self._save_env_variable('USE_REFLECTION', 'true' if checked else 'false'))
        reflection_layout.addWidget(self.reflection_toggle)
        reflection_layout.addStretch()
        parent_layout.addLayout(reflection_layout)
        
        parent_layout.addSpacing(12)
        
        # OLLAMA_ENABLED
        ollama_label = QLabel("Usa Ollama (LLM locale)")
        ollama_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(ollama_label)
        
        ollama_desc = QLabel("Connetti a un server Ollama locale invece di usare Google Gemini")
        ollama_desc.setStyleSheet(f"""
            font-size: 12px;
            color: {get_caption_text_color()};
            padding-bottom: 8px;
        """)
        parent_layout.addWidget(ollama_desc)
        
        ollama_layout = QHBoxLayout()
        self.ollama_toggle = ToggleSwitch()
        self.ollama_toggle.toggled.connect(lambda checked: self._save_env_variable('OLLAMA_ENABLED', 'true' if checked else 'false'))
        ollama_layout.addWidget(self.ollama_toggle)
        ollama_layout.addStretch()
        parent_layout.addLayout(ollama_layout)
        
        parent_layout.addSpacing(12)
        
        # OLLAMA_BASE_URL
        ollama_url_label = QLabel("Ollama Base URL")
        ollama_url_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(ollama_url_label)
        
        self.ollama_url_input = QLineEdit()
        self.ollama_url_input.setPlaceholderText("http://localhost:11434")
        self.ollama_url_input.setMinimumHeight(44)
        self.ollama_url_input.textChanged.connect(lambda text: self._save_env_variable('OLLAMA_BASE_URL', text.strip()))
        parent_layout.addWidget(self.ollama_url_input)
        
        parent_layout.addSpacing(12)
        
        # OLLAMA_MODEL
        ollama_model_label = QLabel("Ollama Model Name")
        ollama_model_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(ollama_model_label)
        
        self.ollama_model_input = QLineEdit()
        self.ollama_model_input.setPlaceholderText("llama3.2:latest")
        self.ollama_model_input.setMinimumHeight(44)
        self.ollama_model_input.textChanged.connect(lambda text: self._save_env_variable('OLLAMA_MODEL', text.strip()))
        parent_layout.addWidget(self.ollama_model_input)
    
    def toggle_api_visibility(self):
        """Toggle della visibilità dell'API key"""
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
    
    def on_api_key_changed(self, text):
        """Salva automaticamente l'API key nel file .env quando cambia il contenuto"""
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
        
        # Carica impostazioni Power User
        use_rag = get_env_bool('USE_RAG', True)
        self.rag_toggle.setChecked(use_rag)
        
        use_reflection = get_env_bool('USE_REFLECTION', True)
        self.reflection_toggle.setChecked(use_reflection)
        
        ollama_enabled = get_env_bool('OLLAMA_ENABLED', False)
        self.ollama_toggle.setChecked(ollama_enabled)
        
        ollama_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_url_input.setText(ollama_url)
        
        ollama_model = os.environ.get('OLLAMA_MODEL', 'llama3.2:latest')
        self.ollama_model_input.setText(ollama_model)
