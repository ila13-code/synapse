"""
Sistema di icone basato su QtAwesome (Font Awesome 6) per Synapse
QtAwesome fornisce icone Font Awesome bellissime per PyQt
"""

try:
    import qtawesome as qta
    QTAWESOME_AVAILABLE = True
except ImportError:
    QTAWESOME_AVAILABLE = False
    print("⚠️  QtAwesome non installato. Installa con: pip install QtAwesome")

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt


class IconProvider:
    """
    Provider di icone Font Awesome tramite QtAwesome
    Molto più belle e professionali!
    """
    
    # Mappa nomi semplici -> Font Awesome icon names
    ICON_MAP = {
        # Icone principali
        'book': 'fa5s.book-open',
        'plus': 'fa5s.plus-circle',
        'settings': 'fa5s.cog',
        'brain': 'fa5s.brain',
        
        # File e documenti  
        'document': 'fa5s.file-alt',
        'file_text': 'fa5s.file-alt',
        'folder': 'fa5s.folder',
        
        # AI e generazione
        'sparkles': 'fa5s.magic',
        'wand': 'fa5s.magic',
        
        # Flashcard
        'cards': 'fa5s.layer-group',
        
        # Upload/Download
        'upload': 'fa5s.cloud-upload-alt',
        'download': 'fa5s.download',
        
        # Azioni
        'trash': 'fa5s.trash-alt',
        'edit': 'fa5s.edit',
        'save': 'fa5s.save',
        
        # Navigazione
        'arrow-left': 'fa5s.arrow-left',
        'arrow-right': 'fa5s.arrow-right',
        
        # UI
        'check': 'fa5s.check-circle',
        'info': 'fa5s.info-circle',
        
        # Sicurezza
        'key': 'fa5s.key',
        'eye': 'fa5s.eye',
        'eye-slash': 'fa5s.eye-slash',
        
        # Varie
        'rotate': 'fa5s.sync-alt',
        'globe': 'fa5s.globe',
    }
    
    @classmethod
    def get_icon(cls, icon_name: str, size: int = 24, color: str = '#000000') -> QIcon:
        """Ottiene un'icona per QPushButton"""
        if not QTAWESOME_AVAILABLE:
            return QIcon()
        
        fa_name = cls.ICON_MAP.get(icon_name, 'fa5s.question-circle')
        return qta.icon(fa_name, color=color)
    
    @classmethod
    def get_colored_icon_label(cls, icon_name: str, color: str = '#8B5CF6', size: int = 32) -> str:
        """Per compatibilità - usa setup_icon_label invece"""
        return ""
    
    @classmethod
    def setup_icon_label(cls, label: QLabel, icon_name: str, size: int = 32, color: str = '#8B5CF6'):
        """Configura un QLabel con icona Font Awesome"""
        if not QTAWESOME_AVAILABLE:
            label.setText("?")
            return
        
        fa_name = cls.ICON_MAP.get(icon_name, 'fa5s.question-circle')
        icon = qta.icon(fa_name, color=color)
        pixmap = icon.pixmap(size, size)
        
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("background: transparent; border: none;")