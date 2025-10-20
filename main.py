import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from database.db_manager import DatabaseManager
from config.env_loader import load_env

def main():
    # Carica variabili d'ambiente
    load_env()
    
    # Crea applicazione
    app = QApplication(sys.argv)
    app.setApplicationName("Synapse")
    app.setOrganizationName("Synapse")
    
    # Inizializza il database
    db = DatabaseManager()
    db.init_db()
    
    # Crea e mostra la finestra principale
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()