"""
Stili CSS per l'applicazione Synapse
Replica il design system dell'interfaccia web originale
"""

MAIN_STYLE = """
QMainWindow {
    background-color: #FAFAFA;
}

/* Header */
QWidget#header {
    background-color: white;
    border-bottom: 1px solid #E8E8E8;
}

/* Cards */
/* Cards */
QFrame.card {
    background-color: white;
    border: 1px solid #E8E8E8;
    border-radius: 16px;
}

QFrame.card:hover {
    border-color: #8B5CF6;
}


QLabel.card_text {
    background-color: transparent;
    border: none;
    padding: 0px;
    margin: 0px;
}
/* Buttons */
QPushButton.primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #8B5CF6, stop:1 #3B82F6);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 600;
    font-size: 14px;
}

QPushButton.primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #7C3AED, stop:1 #2563EB);
}

QPushButton.primary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #6D28D9, stop:1 #1D4ED8);
}

QPushButton.primary:disabled {
    background: #D4D4D4;
    color: #A3A3A3;
}

QPushButton.secondary {
    background-color: white;
    color: #262626;
    border: 1px solid #E8E8E8;
    border-radius: 12px;
    padding: 10px 20px;
    font-weight: 500;
    font-size: 14px;
}

QPushButton.secondary:hover {
    background-color: #F5F5F5;
}

QPushButton.secondary:pressed {
    background-color: #E5E5E5;
}

QPushButton.icon-button {
    background-color: transparent;
    border: none;
    padding: 8px;
    border-radius: 8px;
}

QPushButton.icon-button:hover {
    background-color: #F5F5F5;
}

/* Input Fields */
QLineEdit, QTextEdit {
    background-color: white;
    border: 1px solid #E8E8E8;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 14px;
    color: #262626;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #8B5CF6;
    outline: none;
}

QLineEdit::placeholder, QTextEdit::placeholder {
    color: #A3A3A3;
}

/* Labels */
QLabel.title {
    font-size: 24px;
    font-weight: 700;
    color: #171717;
}

QLabel.subtitle {
    font-size: 16px;
    font-weight: 600;
    color: #262626;
}

QLabel.body {
    font-size: 14px;
    color: #525252;
}

QLabel.caption {
    font-size: 12px;
    color: #737373;
}

/* Tab Widget */
QTabWidget::pane {
    border: none;
    background-color: transparent;
}

QTabBar::tab {
    background-color: transparent;
    color: #737373;
    padding: 12px 24px;
    border: none;
    border-radius: 10px;
    margin-right: 4px;
    font-weight: 500;
    font-size: 14px;
}

QTabBar::tab:selected {
    background-color: white;
    color: #8B5CF6;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #F5F5F5;
}

/* ScrollArea */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background-color: #F5F5F5;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #D4D4D4;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #A3A3A3;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #F5F5F5;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #D4D4D4;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #A3A3A3;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ComboBox */
QComboBox {
    background-color: white;
    border: 1px solid #E8E8E8;
    border-radius: 12px;
    padding: 8px 12px;
    font-size: 14px;
}

QComboBox:focus {
    border: 2px solid #8B5CF6;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #737373;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #E8E8E8;
    border-radius: 8px;
    selection-background-color: #F3F4F6;
    selection-color: #171717;
    padding: 4px;
}

/* Dialog */
QDialog {
    background-color: white;
}

/* MessageBox */
QMessageBox {
    background-color: white;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 8px 16px;
}

/* Progress Dialog */
QProgressDialog {
    background-color: white;
}
"""

# Colori predefiniti per le materie
SUBJECT_COLORS = [
    '#8B5CF6',  # Viola
    '#3B82F6',  # Blu
    '#10B981',  # Verde
    '#F59E0B',  # Arancione
    '#EF4444',  # Rosso
    '#EC4899',  # Rosa
]

DIFFICULTY_COLORS = {
    'easy': '#10B981',    # Verde
    'medium': '#F59E0B',  # Arancione
    'hard': '#EF4444',    # Rosso
}