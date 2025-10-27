from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QScrollArea, QGridLayout, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont
from database.db_manager import DatabaseManager
# Importa le funzioni tema
from ui.styles import (get_theme_style, get_theme_colors, get_text_color, 
                       get_secondary_text_color, get_caption_text_color, get_icon_color, get_card_background) 
from ui.dialogs import CreateSubjectDialog, SettingsDialog
from ui.subject_window import SubjectWindow
from ui.icons import IconProvider

class SubjectCard(QFrame):
    """Widget per visualizzare una card materia"""
    
    def __init__(self, subject_data, parent=None):
        super().__init__(parent)
        self.subject_data = subject_data
        self.parent_window = parent
        self.setup_ui()
        
    def setup_ui(self):
        accent_color = self.subject_data['color']
        text_color = get_text_color()
        card_bg = get_card_background()
        
        # Ottieni il tema per decidere il colore hover
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            theme = db.get_setting('theme', 'light')
        except:
            theme = 'light'
        
        # Hover diverso per light e dark mode
        if theme == 'dark':
            hover_bg = "#222222"
        else:
            hover_bg = "#F5F5F5"

        self.setFixedSize(280, 200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Styling pulito e professionale per le card
        self.setStyleSheet(f"""
            SubjectCard {{
                background-color: {card_bg};
                border: 1px solid {get_caption_text_color()}50; 
                border-left: 4px solid {accent_color};
                border-radius: 12px;
            }}
            SubjectCard:hover {{
                border: 1px solid {accent_color};
                border-left: 4px solid {accent_color};
                background-color: {hover_bg}; 
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header con icona e pulsante elimina
        header_layout = QHBoxLayout()
        header_layout.setSpacing(0)
        
        # Icona del libro con colore della materia
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, 'book', 32, accent_color)
        header_layout.addWidget(icon_label)
        
        header_layout.addStretch()
        
        # Pulsante elimina - Colore icona e hover sensibili al tema
        delete_btn = QPushButton()
        delete_btn.setIcon(IconProvider.get_icon('trash', 16, '#EF4444'))
        delete_btn.setProperty("class", "icon-button")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setToolTip("Elimina materia")
        delete_btn.clicked.connect(self.delete_subject)
        # Sovrascrive lo stile generale solo per il colore hover del tasto rosso
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: #EF444430; /* Rosso con opacità */
            }}
        """)
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        layout.addStretch()
        
        # Nome materia - Usa get_text_color()
        name_label = QLabel(self.subject_data['name'])
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"""
            font-size: 18px; 
            font-weight: 700; 
            color: {text_color};
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        layout.addWidget(name_label)
        
        # Descrizione (se presente) - Usa get_secondary_text_color()
        if self.subject_data.get('description'):
            desc_label = QLabel(self.subject_data['description'])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"""
                font-size: 13px; 
                color: {get_secondary_text_color()};
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            """)
            layout.addWidget(desc_label)
        else:
            layout.addSpacing(18)
        
        # Data creazione - Usa get_caption_text_color()
        date_label = QLabel(f"Creata il {self.subject_data['created_at'][:10]}")
        date_label.setStyleSheet(f"""
            font-size: 11px; 
            color: {get_caption_text_color()};
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        """)
        layout.addWidget(date_label)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Verifica che il clic non sia sul pulsante elimina
            child = self.childAt(event.pos())
            if not child or (not isinstance(child, QPushButton) and child != self.parent_window.findChild(QPushButton, "delete_btn")):
                self.open_subject()
            
    def open_subject(self):
        """Apre la finestra della materia"""
        self.subject_window = SubjectWindow(self.subject_data, self) # Passa SubjectCard come parent
        self.subject_window.show()
    
    def delete_subject(self):
        """Elimina la materia dopo conferma"""
        # ... (il codice di delete_subject rimane invariato)
        reply = QMessageBox.question(
            self,
            'Conferma Eliminazione',
            f'Sei sicuro di voler eliminare la materia "{self.subject_data["name"]}"?\n\n'
            f'Verranno eliminati anche tutti i documenti e le flashcard associati.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db = DatabaseManager()
                db.delete_subject(self.subject_data['id'])
                
                # Aggiorna la visualizzazione della finestra principale
                if self.parent_window:
                    self.parent_window.load_subjects()
                
                QMessageBox.information(
                    self,
                    'Materia Eliminata',
                    f'La materia "{self.subject_data["name"]}" è stata eliminata con successo.'
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Errore',
                    f'Errore durante l\'eliminazione della materia:\n{str(e)}'
                )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.subject_windows = [] 
        self.setup_ui()
        self.load_subjects()
    
    # Nuovo metodo per applicare il tema in tempo reale
    def apply_theme(self):
        """Applica lo stile del tema corrente immediatamente"""
        self.setStyleSheet(get_theme_style())
        # Forza la ricarica dei widget sensibili al tema
        self.load_subjects() # Le SubjectCard ricaricheranno i loro stili
        self.update() 
        
        # Ricarica l'header per gli stili hardcodati al suo interno
        header = self.centralWidget().layout().itemAt(0).widget()
        self.centralWidget().layout().replaceWidget(header, self.create_header())
        header.deleteLater()
        
    def setup_ui(self):
        self.setWindowTitle("Synapse - AI Flashcard Generator")
        self.setMinimumSize(1200, 800)
        
        self.setStyleSheet(get_theme_style())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Content
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
        title_layout.setSpacing(12)
        
        # Logo con icona brain - Usa colori tema
        logo_label = QLabel()
        # Colore primario hardcodato (Purple/Viola)
        primary_color = '#8B5CF6' 
        IconProvider.setup_icon_label(logo_label, 'brain', 28, primary_color)
        title_layout.addWidget(logo_label)
        
        # Titolo - Usa colori tema
        title_label = QLabel("Synapse")
        title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {primary_color};
        """)
        title_layout.addWidget(title_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Bottone impostazioni con icona - Usa colori tema
        settings_btn = QPushButton(" Impostazioni")
        settings_btn.setIcon(IconProvider.get_icon('settings', 18, get_icon_color())) # Usa get_icon_color()
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
        
        # Header sezione
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # I QLabel.title e QLabel.body sono gestiti in styles.py
        title = QLabel("Le tue Materie")
        title.setProperty("class", "title")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Organizza il tuo studio creando materie e generando flashcard con l'AI")
        subtitle.setProperty("class", "body")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)

        # Scroll area per le card
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
        
        centering_layout.addWidget(grid_wrapper, alignment=Qt.AlignmentFlag.AlignCenter)

        # Card "Nuova Materia"
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
        
        # Usa le funzioni tema per i colori
        primary_color = '#8B5CF6'
        card_bg = get_card_background()
        theme = self.db.get_setting('theme', 'light')
        
        # Hover diverso per light e dark mode
        if theme == 'dark':
            hover_bg = "#222222"
        else:
            hover_bg = "#F5F5F5"
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 2px dashed {get_caption_text_color()}50;
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {hover_bg};
                border: 2px dashed {primary_color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        # Icona plus - Usa colori tema
        icon_label = QLabel()
        IconProvider.setup_icon_label(icon_label, 'plus', 48, primary_color)
        layout.addWidget(icon_label)
        
        # Testo principale - Usa get_text_color()
        text_label = QLabel("Nuova Materia")
        text_label.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: 600; 
            color: {get_text_color()};
            background: transparent;
            border: none;
        """)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
        
        # Descrizione - Usa get_caption_text_color()
        desc_label = QLabel("Crea una nuova cartella di studio")
        desc_label.setStyleSheet(f"""
            font-size: 13px; 
            color: {get_caption_text_color()};
            background: transparent;
            border: none;
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        card.mousePressEvent = lambda e: self.create_subject()
        
        return card
    
    def load_subjects(self):
        """Carica e visualizza tutte le materie"""
        subjects = self.db.get_all_subjects()

        # Rimuovi tutte le card tranne quella "Nuova Materia" in posizione (0,0)
        # Rimuovi tutte le card tranne la card di creazione che è l'unica con item_index=0
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            widget = item.widget()
            
            # Non rimuovere la card "Nuova Materia"
            if widget and widget.inherits('QFrame') and 'Nuova Materia' in widget.findChild(QLabel).text():
                continue

            if item:
                self.grid_layout.removeItem(item)
                if item.widget():
                    item.widget().deleteLater()
        
        # Ricarica la card "Nuova Materia" per applicare il tema
        new_card_item = self.grid_layout.itemAtPosition(0, 0)
        if new_card_item and new_card_item.widget():
            new_card_widget = new_card_item.widget()
            self.grid_layout.removeWidget(new_card_widget)
            new_card_widget.deleteLater()
        
        create_card = self.create_new_subject_card()
        self.grid_layout.addWidget(create_card, 0, 0)

        COLUMNS = 4
        
        # Aggiungi le card delle materie
        for idx, subject in enumerate(subjects):
            # Passiamo SubjectCard la MainWindow come parent_window per il ricaricamento
            card = SubjectCard(subject, self) 

            item_index = idx + 1
            row = item_index // COLUMNS
            col = item_index % COLUMNS
            
            self.grid_layout.addWidget(card, row, col)
        
        # Assicura che la griglia riempia lo spazio in larghezza
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
        # Connessione per l'hot reload del tema
        dialog.theme_changed.connect(self.apply_theme) 
        dialog.exec()