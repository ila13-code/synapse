import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from config.env_loader import load_env
from database.db_manager import DatabaseManager
from ui.main_window import MainWindow
from ui.styles import get_background_color, get_text_color, get_theme_style


def main():
    # Carica variabili d'ambiente
    load_env()
    
    # Crea applicazione
    app = QApplication(sys.argv)
    app.setApplicationName("Synapse")
    app.setOrganizationName("Synapse")
    # Forza il tema light a livello di applicazione
    try:
        # Applica lo stylesheet light globalmente
        app.setStyleSheet(get_theme_style())

        # Costruisci una palette chiara coerente con i colori del tema
        palette = QPalette()
        bg = QColor(get_background_color())
        text = QColor(get_text_color())
        palette.setColor(QPalette.ColorRole.Window, bg)
        palette.setColor(QPalette.ColorRole.Base, QColor('white'))
        palette.setColor(QPalette.ColorRole.Button, QColor('white'))
        palette.setColor(QPalette.ColorRole.WindowText, text)
        palette.setColor(QPalette.ColorRole.Text, text)
        palette.setColor(QPalette.ColorRole.ButtonText, text)
        palette.setColor(QPalette.ColorRole.Highlight, QColor('#8B5CF6'))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor('white'))
        app.setPalette(palette)
    except Exception:
        # Non bloccante: se qualcosa fallisce continuiamo comunque
        pass
    
    # Inizializza il database
    db = DatabaseManager()
    db.init_db()
    
    # Crea e mostra la finestra principale
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()