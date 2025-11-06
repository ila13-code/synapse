"""
Stili CSS Dark Mode per l'applicazione Synapse
Palette scura professionale e moderna
"""

DARK_STYLE = """
QMainWindow {
    background-color: #0F0F0F;
}

/* Header */
QWidget#header {
    background-color: #1A1A1A;
    border-bottom: 1px solid #2A2A2A;
}

/* Cards - DARK MODE VERA */
QFrame.card, SubjectCard {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 12px;
}

QFrame.card:hover, SubjectCard:hover {
    border-color: #8B5CF6;
    background-color: #222222;
}

/* Fix per i QLabel dentro le card - TESTO BIANCO */
SubjectCard QLabel {
    background-color: transparent;
    border: none;
    color: #E5E5E5;
}

QFrame.card QLabel {
    background-color: transparent;
    border: none;
    color: #E5E5E5;
}

/* Flashcard styling */
QFrame.flashcard {
    background-color: #1A1A1A;
    border: 2px solid #2A2A2A;
    border-radius: 16px;
    padding: 30px;
}

QFrame.flashcard:hover {
    border-color: #8B5CF6;
}

QFrame.flashcard QLabel {
    color: #E5E5E5;
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
                               stop:0 #9D6FFF, stop:1 #4A9AFF);
}

QPushButton.primary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #7C3AED, stop:1 #2563EB);
}

QPushButton.primary:disabled {
    background: #2A2A2A;
    color: #525252;
}

QPushButton.secondary {
    background-color: #1A1A1A;
    color: #E5E5E5;
    border: 1px solid #2A2A2A;
    border-radius: 12px;
    padding: 10px 20px;
    font-weight: 500;
    font-size: 14px;
}

QPushButton.secondary:hover {
    background-color: #262626;
    border-color: #3A3A3A;
}

QPushButton.secondary:pressed {
    background-color: #2A2A2A;
}

QPushButton.icon-button {
    background-color: transparent;
    border: none;
    padding: 8px;
    border-radius: 8px;
}

QPushButton.icon-button:hover {
    background-color: #262626;
}

/* Input Fields */
QLineEdit, QTextEdit {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 14px;
    color: #E5E5E5;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #8B5CF6;
    outline: none;
}

QLineEdit:read-only, QTextEdit:read-only {
    border: none;
    background-color: transparent;
    padding: 0;
}

QLineEdit::placeholder, QTextEdit::placeholder {
    color: #525252;
}

/* Labels - BIANCHI E GRIGIO MOLTO CHIARO */
QLabel {
    color: #FFFFFF;
}

QLabel.title {
    font-size: 24px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel.subtitle {
    font-size: 16px;
    font-weight: 600;
    color: #E5E5E5;
}

QLabel.body {
    font-size: 14px;
    color: #E5E5E5;
}

QLabel.caption {
    font-size: 12px;
    color: #D1D1D1;
}

/* Tab Widget - DARK */
QTabWidget::pane {
    border: none;
    background-color: transparent;
    border-top: 2px solid #2A2A2A;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: transparent;
    color: #D1D1D1;
    padding: 16px 28px;
    border: none;
    border-bottom: 3px solid transparent;
    margin-right: 8px;
    font-weight: 600;
    font-size: 15px;
    min-width: 100px;
}

QTabBar::tab:selected {
    background-color: transparent;
    color: #FFFFFF;
    border-bottom: 3px solid #8B5CF6;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(139, 92, 246, 0.1);
    color: #E5E5E5;
    border-bottom: 3px solid rgba(139, 92, 246, 0.3);
}

/* ScrollArea */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background-color: #1A1A1A;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #3A3A3A;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4A4A4A;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background-color: #1A1A1A;
    height: 10px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #3A3A3A;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4A4A4A;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ComboBox */
QComboBox {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 12px;
    padding: 8px 12px;
    font-size: 14px;
    color: #E5E5E5;
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
    border-top: 6px solid #E5E5E5;
    margin-right: 5px;
}

QComboBox QAbstractItemView {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    selection-background-color: #262626;
    selection-color: #F5F5F5;
    color: #E5E5E5;
    padding: 4px;
}

/* Checkbox */
QCheckBox {
    spacing: 8px;
    font-size: 14px;
    color: #E5E5E5;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 2px solid #2A2A2A;
    background-color: #1A1A1A;
}

QCheckBox::indicator:hover {
    border-color: #8B5CF6;
}

QCheckBox::indicator:checked {
    background-color: #8B5CF6;
    border-color: #8B5CF6;
}

/* Dialog */
QDialog {
    background-color: #1A1A1A;
}

QDialog QLabel {
    color: #E5E5E5;
}

/* MessageBox */
QMessageBox {
    background-color: #1A1A1A;
    color: #E5E5E5;
}

QMessageBox QLabel {
    color: #E5E5E5;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 8px 16px;
}

/* Progress Dialog */
QProgressDialog {
    background-color: #1A1A1A;
    color: #E5E5E5;
}

QProgressDialog QLabel {
    color: #E5E5E5;
}

QProgressBar {
    border: none;
    border-radius: 8px;
    background-color: #262626;
    text-align: center;
    font-size: 12px;
    color: #E5E5E5;
}

QProgressBar::chunk {
    border-radius: 8px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #8B5CF6, stop:1 #3B82F6);
}

/* File Dialog */
QFileDialog {
    background-color: #1A1A1A;
}

QFileDialog QPushButton {
    min-width: 80px;
    padding: 8px 16px;
}

QFileDialog QListView, QFileDialog QTreeView, QFileDialog QTableView {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    color: #E5E5E5;
    selection-background-color: #262626;
    selection-color: #FFFFFF;
}

QFileDialog QLineEdit {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    padding: 6px 12px;
    color: #E5E5E5;
}

QFileDialog QComboBox {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    padding: 6px 12px;
    color: #E5E5E5;
}

QFileDialog QLabel {
    color: #E5E5E5;
}

/* EXTRA - Area contenuti centrale */
QWidget {
    background-color: #0F0F0F;
    color: #E5E5E5;
}

QScrollArea > QWidget > QWidget {
    background-color: #0F0F0F;
}
"""

# Colori predefiniti per le materie (più luminosi per dark mode)
SUBJECT_COLORS_DARK = [
    '#9D6FFF',  # Viola più chiaro
    '#5B9FFF',  # Blu più chiaro
    '#34D399',  # Verde più chiaro
    '#FBBF24',  # Arancione più chiaro
    '#F87171',  # Rosso più chiaro
    '#F472B6',  # Rosa più chiaro
]

DIFFICULTY_COLORS_DARK = {
    'easy': '#34D399',    # Verde
    'medium': '#FBBF24',  # Arancione
    'hard': '#F87171',    # Rosso
}