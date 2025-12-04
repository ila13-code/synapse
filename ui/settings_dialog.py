import os

from PyQt6.QtCore import QFileSystemWatcher, Qt
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
    """Settings Dialog (API Key)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        # Flag to avoid update loops
        self.updating_api_key = False
        self.power_user_mode = False
        # Load saved power user mode state
        self.load_power_user_mode_state()
        self.setup_ui()
        self.load_settings()
        
        # Watcher for .env file
        self.env_watcher = QFileSystemWatcher()
        env_path = os.path.abspath('.env')
        if os.path.exists(env_path):
            self.env_watcher.addPath(env_path)
        self.env_watcher.fileChanged.connect(self.on_env_file_changed)
    
    def setup_ui(self):
        self.setWindowTitle("Settings")
        # Set fixed size based on mode
        if self.power_user_mode:
            self.setFixedSize(1300, 800)
        else:
            self.setFixedSize(1300, 450)
        self.setModal(True)
        
        # Center window on screen
        self.center_on_screen()
        
        # Apply ONLY light theme
        from ui.styles import MAIN_STYLE
        self.setStyleSheet(MAIN_STYLE)
        
        # Scroll area to contain all settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Header with mode toggle
        self.create_mode_toggle(layout)
        
        # Container for API Keys (base mode: 2 columns)
        self.api_keys_container = QWidget()
        self.api_keys_layout = QGridLayout(self.api_keys_container)
        self.api_keys_layout.setSpacing(20)
        self.api_keys_layout.setColumnStretch(0, 1)
        self.api_keys_layout.setColumnStretch(1, 1)
        
        # Left column: Gemini API Key
        self.gemini_col = QWidget()
        self.gemini_layout = QVBoxLayout(self.gemini_col)
        self.gemini_layout.setContentsMargins(0, 0, 0, 0)
        self.gemini_layout.setSpacing(20)
        self.create_gemini_api_key_section(self.gemini_layout)
        self.api_keys_layout.addWidget(self.gemini_col, 0, 0)
        
        # Right column: Tavily API Key
        self.tavily_col = QWidget()
        self.tavily_layout = QVBoxLayout(self.tavily_col)
        self.tavily_layout.setContentsMargins(0, 0, 0, 0)
        self.tavily_layout.setSpacing(20)
        self.create_tavily_api_key_section(self.tavily_layout)
        self.api_keys_layout.addWidget(self.tavily_col, 0, 1)
        
        layout.addWidget(self.api_keys_container)
        
        # Container for Power User (initially hidden)
        self.power_user_widget = QWidget()
        self.power_user_layout = QGridLayout(self.power_user_widget)
        self.power_user_layout.setContentsMargins(0, 0, 0, 0)
        self.power_user_layout.setSpacing(20)
        self.power_user_layout.setColumnStretch(0, 1)
        self.power_user_layout.setColumnStretch(1, 1)
        self.power_user_layout.setColumnStretch(2, 1)
        self.create_power_user_section(self.power_user_layout)
        # Show/hide based on saved mode
        self.power_user_widget.setVisible(self.power_user_mode)
        layout.addWidget(self.power_user_widget)
        layout.addStretch()
        
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def create_mode_toggle(self, parent_layout):
        """Create toggle for Base/Power User mode"""
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
        
        title = QLabel("Settings")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {get_text_color()};
        """)
        text_layout.addWidget(title)
        
        subtitle = QLabel("Base Mode" if not self.power_user_mode else "Power User Mode - Advanced Settings")
        subtitle.setStyleSheet(f"""
            font-size: 13px;
            color: {get_caption_text_color()};
        """)
        text_layout.addWidget(subtitle)
        self.mode_subtitle = subtitle
        
        mode_layout.addLayout(text_layout)
        mode_layout.addStretch()
        
        # Toggle for Power User mode
        mode_label = QLabel("Power User")
        mode_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {get_secondary_text_color()};
        """)
        mode_layout.addWidget(mode_label)
        
        self.mode_toggle = ToggleSwitch()
        self.mode_toggle.setChecked(self.power_user_mode, animate=False)  # Set saved state
        self.mode_toggle.toggled.connect(self.toggle_power_user_mode)
        mode_layout.addWidget(self.mode_toggle)
        
        parent_layout.addWidget(mode_frame)
    
    def toggle_power_user_mode(self, checked):
        """Enable/disable Power User mode"""
        self.power_user_mode = checked
        self.power_user_widget.setVisible(checked)
        
        # Update subtitle
        if checked:
            self.mode_subtitle.setText("Power User Mode - Advanced Settings")
            # Fixed size for Power User mode
            self.setFixedSize(1300, 800)
        else:
            self.mode_subtitle.setText("Base Mode")
            # Fixed size for Base mode
            self.setFixedSize(1300, 450)
        
        # Save power user mode state
        self.save_power_user_mode_state()
        
        # Re-center window after resizing
        self.center_on_screen()
    
    def create_gemini_api_key_section(self, parent_layout):
        """Create Google Gemini API Key section"""
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
            f'Get your API key</a>'
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
        self.api_input.setPlaceholderText("Enter your API key...")
        self.api_input.setMinimumHeight(44)
        self.api_input.textChanged.connect(self.on_api_key_changed)
        input_layout.addWidget(self.api_input)
        
        # Show/hide button
        self.show_btn = QPushButton()
        self.show_btn.setIcon(IconProvider.get_icon('eye', 16, get_icon_color()))
        self.show_btn.setProperty("class", "secondary")
        self.show_btn.setFixedWidth(100)
        self.show_btn.setMinimumHeight(44)
        self.show_btn.clicked.connect(self.toggle_api_visibility)
        input_layout.addWidget(self.show_btn)
        
        # Trash button to delete API key
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
    
    def create_tavily_api_key_section(self, parent_layout):
        """Create Tavily API Key section"""
        # Tavily API Key
        tavily_label = QLabel("Tavily API Key (optional)")
        tavily_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        parent_layout.addWidget(tavily_label)
        
        tavily_link_label = QLabel(
            f'<a href="https://tavily.com/" '
            f'style="color: #8B5CF6; text-decoration: underline;">'
            f'Get your API key</a> - for advanced web search'
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
        self.tavily_api_input.setPlaceholderText("Enter your Tavily API key...")
        self.tavily_api_input.setMinimumHeight(44)
        self.tavily_api_input.textChanged.connect(self.on_tavily_api_key_changed)
        tavily_input_layout.addWidget(self.tavily_api_input)
        
        # Show/hide button for Tavily
        self.show_tavily_btn = QPushButton()
        self.show_tavily_btn.setIcon(IconProvider.get_icon('eye', 16, get_icon_color()))
        self.show_tavily_btn.setProperty("class", "secondary")
        self.show_tavily_btn.setFixedWidth(100)
        self.show_tavily_btn.setMinimumHeight(44)
        self.show_tavily_btn.clicked.connect(self.toggle_tavily_api_visibility)
        tavily_input_layout.addWidget(self.show_tavily_btn)
        
        # Trash button to delete Tavily API key
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
        """Create section with advanced parameters for Power User in 3 columns"""
        # Section title spanning all 3 columns
        power_title = QLabel("⚡ Advanced Settings")
        power_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: #8B5CF6;
            padding: 8px 0;
        """)
        parent_layout.addWidget(power_title, 0, 0, 1, 3)  # Span 3 columns
        
        # COLUMN 1: RAG and Reflection
        col1 = QWidget()
        col1_layout = QVBoxLayout(col1)
        col1_layout.setContentsMargins(0, 0, 0, 0)
        col1_layout.setSpacing(12)
        
        # USE_RAG
        rag_label = QLabel("Enable RAG")
        rag_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        col1_layout.addWidget(rag_label)
        
        rag_desc = QLabel("Retrieval-Augmented Generation\nImproves generation using semantic search")
        rag_desc.setWordWrap(True)
        rag_desc.setStyleSheet(f"""
            font-size: 12px;
            color: {get_caption_text_color()};
            padding-bottom: 8px;
        """)
        col1_layout.addWidget(rag_desc)
        
        rag_toggle_layout = QHBoxLayout()
        self.rag_toggle = ToggleSwitch()
        self.rag_toggle.toggled.connect(lambda checked: self._save_env_variable('USE_RAG', 'true' if checked else 'false'))
        rag_toggle_layout.addWidget(self.rag_toggle)
        rag_toggle_layout.addStretch()
        col1_layout.addLayout(rag_toggle_layout)
        
        col1_layout.addSpacing(20)
        
        # USE_REFLECTION
        reflection_label = QLabel("Enable Reflection")
        reflection_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        col1_layout.addWidget(reflection_label)
        
        reflection_desc = QLabel("Iterative self-critique process\nto improve quality")
        reflection_desc.setWordWrap(True)
        reflection_desc.setStyleSheet(f"""
            font-size: 12px;
            color: {get_caption_text_color()};
            padding-bottom: 8px;
        """)
        col1_layout.addWidget(reflection_desc)
        
        reflection_toggle_layout = QHBoxLayout()
        self.reflection_toggle = ToggleSwitch()
        self.reflection_toggle.toggled.connect(lambda checked: self._save_env_variable('USE_REFLECTION', 'true' if checked else 'false'))
        reflection_toggle_layout.addWidget(self.reflection_toggle)
        reflection_toggle_layout.addStretch()
        col1_layout.addLayout(reflection_toggle_layout)
        
        col1_layout.addStretch()
        parent_layout.addWidget(col1, 1, 0)
        
        # COLUMN 2: Local LLM Enable/Disable
        col2 = QWidget()
        col2_layout = QVBoxLayout(col2)
        col2_layout.setContentsMargins(0, 0, 0, 0)
        col2_layout.setSpacing(12)
        
        # USE_LOCAL_LLM
        local_llm_label = QLabel("Use Local LLM")
        local_llm_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        col2_layout.addWidget(local_llm_label)
        
        local_llm_desc = QLabel("Local LLM\nConnect to a local LLM server (e.g. Ollama, LM Studio) instead of Google Gemini")
        local_llm_desc.setWordWrap(True)
        local_llm_desc.setStyleSheet(f"""
            font-size: 12px;
            color: {get_caption_text_color()};
            padding-bottom: 8px;
        """)
        col2_layout.addWidget(local_llm_desc)
        
        local_llm_toggle_layout = QHBoxLayout()
        self.local_llm_toggle = ToggleSwitch()
        # Connect to handler that shows/hides Local LLM settings
        self.local_llm_toggle.toggled.connect(self.toggle_local_llm_enabled)
        local_llm_toggle_layout.addWidget(self.local_llm_toggle)
        local_llm_toggle_layout.addStretch()
        col2_layout.addLayout(local_llm_toggle_layout)
        
        col2_layout.addStretch()
        parent_layout.addWidget(col2, 1, 1)
        
        # COLUMN 3: Local LLM URL and Model
        col3 = QWidget()
        col3_layout = QVBoxLayout(col3)
        col3_layout.setContentsMargins(0, 0, 0, 0)
        col3_layout.setSpacing(12)
        # Save Local LLM settings widget to show/hide it
        self.local_llm_settings_widget = col3
        
        # LOCAL_LLM_BASE_URL
        local_llm_url_label = QLabel("Local LLM URL")
        local_llm_url_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        col3_layout.addWidget(local_llm_url_label)
        
        self.local_llm_url_input = QLineEdit()
        self.local_llm_url_input.setPlaceholderText("http://localhost:11434")
        self.local_llm_url_input.setMinimumHeight(44)
        self.local_llm_url_input.textChanged.connect(lambda text: self._save_env_variable('LOCAL_LLM_BASE_URL', text.strip()))
        col3_layout.addWidget(self.local_llm_url_input)
        
        col3_layout.addSpacing(20)
        
        # LOCAL_LLM_MODEL
        local_llm_model_label = QLabel("Local LLM Model")
        local_llm_model_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: 600; 
            color: {get_text_color()};
        """)
        col3_layout.addWidget(local_llm_model_label)
        
        self.local_llm_model_input = QLineEdit()
        self.local_llm_model_input.setPlaceholderText("llama3.2:latest")
        self.local_llm_model_input.setMinimumHeight(44)
        self.local_llm_model_input.textChanged.connect(lambda text: self._save_env_variable('LOCAL_LLM_MODEL', text.strip()))
        col3_layout.addWidget(self.local_llm_model_input)
        
        col3_layout.addStretch()
        parent_layout.addWidget(col3, 1, 2)

    def toggle_local_llm_enabled(self, checked: bool):
        """Show or hide Local LLM settings and save preference (if not loading)."""
        # Show/hide URL/Model fields
        try:
            self.local_llm_settings_widget.setVisible(checked)
            # Hide Gemini and Tavily columns if Local LLM is enabled
            self.gemini_col.setVisible(not checked)
            self.tavily_col.setVisible(not checked)
        except Exception:
            # Widget might not be initialized yet
            pass

        # Avoid rewriting .env while loading settings
        if getattr(self, '_loading_settings', False):
            return

        # Save variable to .env
        self._save_env_variable('USE_LOCAL_LLM', 'true' if checked else 'false')
    
    def toggle_api_visibility(self):
        """Toggle API key visibility"""
        icon_color = get_icon_color()

        if self.api_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_btn.setIcon(IconProvider.get_icon('eye-slash', 16, icon_color))
        else:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_btn.setIcon(IconProvider.get_icon('eye', 16, icon_color))
    
    def toggle_tavily_api_visibility(self):
        """Toggle Tavily API key visibility"""
        icon_color = get_icon_color()

        if self.tavily_api_input.echoMode() == QLineEdit.EchoMode.Password:
            self.tavily_api_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_tavily_btn.setIcon(IconProvider.get_icon('eye-slash', 16, icon_color))
        else:
            self.tavily_api_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_tavily_btn.setIcon(IconProvider.get_icon('eye', 16, icon_color))
    
    def on_api_key_changed(self, text):
        """Automatically save API key to .env when content changes"""
        if self.updating_api_key:
            return
            
        api_key = text.strip()
        
        # Update environment
        if api_key:
            os.environ['GEMINI_API_KEY'] = api_key
        elif 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
        
        # Save to .env
        self._save_env_variable('GEMINI_API_KEY', api_key)
    
    def on_tavily_api_key_changed(self, text):
        """Automatically save Tavily API key to .env when content changes"""
        if self.updating_api_key:
            return
            
        api_key = text.strip()
        
        # Update environment
        if api_key:
            os.environ['TAVILY_API_KEY'] = api_key
        elif 'TAVILY_API_KEY' in os.environ:
            del os.environ['TAVILY_API_KEY']
        
        # Save to .env
        self._save_env_variable('TAVILY_API_KEY', api_key)
    
    def _save_env_variable(self, key: str, value: str):
        """Save an environment variable to .env file and update current environment"""
        # Update current environment
        if value:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]

        try:
            env_path = '.env'
            
            # Read all other existing variables
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
            
            # Write all variables
            with open(env_path, 'w', encoding='utf-8') as f:
                # Write the variable we are saving (if not empty)
                if value:
                    f.write(f'{key}={value}\n')
                # Write all other variables
                for k, v in existing_vars.items():
                    f.write(f'{k}={v}\n')
        except Exception as e:
            print(f"Error saving {key}: {e}")
    
    def on_env_file_changed(self, path):
        """Update textbox when .env file is modified externally"""
        # Re-add file to watcher (needed on some systems)
        if not self.env_watcher.files():
            self.env_watcher.addPath(path)
        
        # Read new value from file
        try:
            self.updating_api_key = True
            api_key = ''
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GEMINI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
            
            # Update textbox only if value changed
            if self.api_input.text() != api_key:
                self.api_input.setText(api_key)
                if api_key:
                    os.environ['GEMINI_API_KEY'] = api_key
        except Exception as e:
            print(f"Error reading .env file: {e}")
        finally:
            self.updating_api_key = False
    
    def delete_gemini_api_key(self):
        """Delete Gemini API key"""
        reply = QMessageBox.question(
            self,
            "Delete API Key",
            "Are you sure you want to delete the Gemini API key?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.api_input.clear()
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']
            self._save_env_variable('GEMINI_API_KEY', '')
    
    def delete_tavily_api_key(self):
        """Delete Tavily API key"""
        reply = QMessageBox.question(
            self,
            "Delete API Key",
            "Are you sure you want to delete the Tavily API key?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.tavily_api_input.clear()
            if 'TAVILY_API_KEY' in os.environ:
                del os.environ['TAVILY_API_KEY']
            self._save_env_variable('TAVILY_API_KEY', '')
    
    def load_settings(self):
        """Load saved settings"""
        # Prevent toggle signals from writing to .env during loading
        self._loading_settings = True
        # Load Gemini API key
        api_key = os.environ.get('GEMINI_API_KEY', '')
        
        # If not present, try reading from .env
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
        
        # Load Tavily API key
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
        
        # Load Power User settings
        use_rag = get_env_bool('USE_RAG', True)
        self.rag_toggle.setChecked(use_rag, animate=False)
        
        use_reflection = get_env_bool('USE_REFLECTION', True)
        self.reflection_toggle.setChecked(use_reflection, animate=False)
        
        use_local_llm = get_env_bool('USE_LOCAL_LLM', False)
        self.local_llm_toggle.setChecked(use_local_llm, animate=False)
        # Show or hide Local LLM settings based on state
        try:
            self.local_llm_settings_widget.setVisible(use_local_llm)
            self.gemini_col.setVisible(not use_local_llm)
            self.tavily_col.setVisible(not use_local_llm)
        except Exception:
            pass
        
        local_llm_url = os.environ.get('LOCAL_LLM_BASE_URL', 'http://localhost:11434')
        self.local_llm_url_input.setText(local_llm_url)
        
        local_llm_model = os.environ.get('LOCAL_LLM_MODEL', 'llama3.2:latest')
        self.local_llm_model_input.setText(local_llm_model)
        # End loading settings
        self._loading_settings = False
    
    def center_on_screen(self):
        """Center window on screen"""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def load_power_user_mode_state(self):
        """Load power user mode state from .env file"""
        try:
            if os.path.exists('.env'):
                with open('.env', 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith('POWER_USER_MODE='):
                            value = line.split('=', 1)[1].strip().lower()
                            self.power_user_mode = value == 'true'
                            break
        except Exception as e:
            print(f"Error loading power user mode state: {e}")
    
    def save_power_user_mode_state(self):
        """Save power user mode state to .env file"""
        self._save_env_variable('POWER_USER_MODE', 'true' if self.power_user_mode else 'false')
