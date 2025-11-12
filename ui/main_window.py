from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                             QMainWindow, QMessageBox, QPushButton,
                             QScrollArea, QStackedWidget, QVBoxLayout, QWidget)

from database.db_manager import DatabaseManager
from ui.dialogs import CreateSubjectDialog, SettingsDialog
from ui.icons import IconProvider
# Importa le funzioni tema
from ui.styles import (get_caption_text_color, get_card_background,
                       get_icon_color, get_secondary_text_color,
                       get_text_color, get_theme_colors, get_theme_style)
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
        text_color = get_text_color()
        card_bg = get_card_background()
        
        # SOLO LIGHT MODE
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
        """Apre la vista della materia sostituendo il contenuto della finestra principale"""
        # Trova la MainWindow
        main_window = self.parent_window
        if main_window and hasattr(main_window, 'show_subject_view'):
            main_window.show_subject_view(self.subject_data)
    
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
        self.current_subject_view = None  # Vista della materia corrente
        self.setup_ui()
        self.load_subjects()
    
    def apply_theme(self):
        """Applica lo stile del tema corrente immediatamente"""
        self.setStyleSheet(get_theme_style())
        # Forza la ricarica dei widget sensibili al tema
        self.load_subjects()  # Le SubjectCard ricaricheranno i loro stili
        self.update() 
        
        # Ricarica l'header per gli stili hardcodati al suo interno
        header = self.findChild(QWidget, "header")
        if header:
            new_header = self.create_header()
            # Trova il layout principale e sostituisci l'header
            main_layout = self.centralWidget().layout()
            if main_layout:
                main_layout.replaceWidget(header, new_header)
                header.deleteLater()
        
        # Se siamo nella vista materia, aggiorna anche quella
        if self.stack.currentIndex() == 1 and self.current_subject_view:
            self.current_subject_view.apply_theme()
    
    def center_on_screen(self):
        """Centra la finestra sullo schermo"""
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def setup_ui(self):
        self.setWindowTitle("Synapse - AI Flashcard Generator")
        self.setMinimumSize(1300, 800)
        
        # Centra la finestra allo schermo
        self.center_on_screen()
        
        self.setStyleSheet(get_theme_style())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Stack Widget per gestire le viste
        self.stack = QStackedWidget()
        
        # Vista 0: Lista materie (contenuto principale)
        subjects_view = self.create_subjects_view()
        self.stack.addWidget(subjects_view)
        
        # Vista 1: Dettaglio materia (verrà popolata dinamicamente)
        # Per ora aggiungiamo un widget placeholder
        placeholder = QWidget()
        self.stack.addWidget(placeholder)
        
        main_layout.addWidget(self.stack)
        
    def create_header(self):
        """Crea l'header dell'applicazione"""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(70)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # Pulsante Indietro (visibile solo nella vista materia)
        self.back_btn = QPushButton()
        self.back_btn.setIcon(IconProvider.get_icon('arrow-left', 20, get_icon_color()))
        self.back_btn.setProperty("class", "secondary")
        self.back_btn.setFixedSize(44, 44)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setToolTip("Torna alle materie")
        self.back_btn.clicked.connect(self.show_subjects_view)
        self.back_btn.hide()  # Nascosto di default
        layout.addWidget(self.back_btn)
        
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        
        # Logo con icona brain - Usa colori tema (nascosto nella vista materia)
        self.logo_label = QLabel()
        # Colore primario hardcodato (Purple/Viola)
        primary_color = '#8B5CF6'
        IconProvider.setup_icon_label(self.logo_label, 'brain', 28, primary_color)
        title_layout.addWidget(self.logo_label)

        # Titolo principale (memorizzato per aggiornamenti quando si apre una materia)
        self.title_label = QLabel("Synapse")
        self.title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {primary_color};
        """)
        title_layout.addWidget(self.title_label)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Bottone impostazioni con icona - Usa colori tema
        settings_btn = QPushButton(" Impostazioni")
        settings_btn.setIcon(IconProvider.get_icon('settings', 18, get_icon_color()))
        settings_btn.setProperty("class", "secondary")
        settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(settings_btn)
        
        return header
    
    def create_subjects_view(self):
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
        
        # Usa le funzioni tema per i colori - SOLO LIGHT
        primary_color = '#8B5CF6'
        card_bg = get_card_background()
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

        # Rimuovi tutte le card esistenti tranne la prima (Nuova Materia)
        while self.grid_layout.count() > 1:
            item = self.grid_layout.takeAt(1)
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
        # Non serve più il collegamento al tema poiché usiamo solo il tema light
        dialog.exec()
    
    def show_subject_view(self, subject_data):
        """Mostra la vista della materia usando lo stack"""
        # Rimuovi la vista precedente se esiste
        if self.current_subject_view:
            old_widget = self.stack.widget(1)
            if old_widget:
                self.stack.removeWidget(old_widget)
                old_widget.deleteLater()
        
        # Crea la nuova vista della materia come widget
        self.current_subject_view = SubjectDetailView(subject_data, self)
        self.stack.insertWidget(1, self.current_subject_view)
        
        # Passa alla vista materia
        self.stack.setCurrentIndex(1)
        
        # Mostra il pulsante Indietro
        self.back_btn.show()
        # Nascondi l'icona del cervello viola di Synapse
        self.logo_label.hide()
        # Aggiorna il titolo con il nome della materia e il colore della materia
        try:
            subject_color = subject_data.get('color', '#8B5CF6')
            self.title_label.setText(subject_data['name'])
            self.title_label.setStyleSheet(f"""
                font-size: 24px;
                font-weight: 700;
                color: {subject_color};
            """)
        except Exception:
            pass
    
    def show_subjects_view(self):
        """Torna alla vista principale delle materie"""
        # Torna alla vista principale
        self.stack.setCurrentIndex(0)
        
        # Nascondi il pulsante Indietro
        self.back_btn.hide()
        # Mostra di nuovo l'icona del cervello viola di Synapse
        self.logo_label.show()
        
        # Ricarica le materie per aggiornare eventuali modifiche
        self.load_subjects()
        # Ripristina il titolo principale con il colore viola originale
        try:
            primary_color = '#8B5CF6'
            self.title_label.setText("Synapse")
            self.title_label.setStyleSheet(f"""
                font-size: 24px;
                font-weight: 700;
                color: {primary_color};
            """)
        except Exception:
            pass


class SubjectDetailView(QWidget):
    """Vista dettaglio di una materia (integrata nella MainWindow)"""
    
    def __init__(self, subject_data, parent=None):
        super().__init__(parent)
        self.subject_data = subject_data
        self.parent_window = parent
        self.db = DatabaseManager()
        
        # Crea la SubjectWindow ma la usiamo come contenuto
        self.subject_window = SubjectWindow(subject_data, self)
        
        # Layout per contenere la SubjectWindow
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Prendi il contenuto centrale dalla SubjectWindow
        subject_content = self.subject_window.centralWidget()
        layout.addWidget(subject_content)
    
    def apply_theme(self):
        """Applica il tema alla vista materia"""
        if self.subject_window:
            self.subject_window.apply_theme()