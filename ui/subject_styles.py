from ui.styles import (get_caption_text_color, get_card_background,
                       get_text_color)


def get_upload_card_style(theme):
    """Stile per la card di upload documenti - SOLO LIGHT"""
    upload_bg = "#FFFFFF"
    border_color = get_caption_text_color()
    
    return f"""
        QFrame {{
            background-color: {upload_bg};
            border: 2px dashed {border_color};
            border-radius: 16px;
        }}
        QFrame:hover {{
            border-color: #8B5CF6;
            background-color: {upload_bg};
        }}
    """


def get_document_card_style(theme):
    """Stile per le card dei documenti - SOLO LIGHT"""
    card_bg = "#FFFFFF"
    hover_bg = "#F5F5F5"
    border_color = get_caption_text_color()
    
    return f"""
        QFrame {{
            background-color: {card_bg};
            border: 1px solid {border_color};
            border-radius: 12px;
        }}
        QFrame:hover {{
            background-color: {hover_bg};
            border-color: #8B5CF6;
        }}
    """


def get_documents_list_bg(theme):
    """Sfondo per la lista documenti - SOLO LIGHT"""
    return "#FAFAFA"


def get_text_label_style(font_size, font_weight="normal"):
    """Stile generico per label di testo"""
    return f"""
        font-size: {font_size}px;
        font-weight: {font_weight};
        color: {get_text_color()};
        border: none;
        background-color: transparent;
    """


def get_caption_label_style(font_size):
    """Stile per label caption/secondarie"""
    return f"""
        font-size: {font_size}px;
        color: {get_caption_text_color()};
        border: none;
        background-color: transparent;
    """


def get_web_search_frame_style():
    """Stile per il frame opzione ricerca web"""
    return f"""
        QFrame {{
            background-color: {get_card_background()};
            border: 1px solid {get_caption_text_color()}30;
            border-radius: 12px;
        }}
    """


def get_flashcard_textedit_style():
    """Stile per il QTextEdit della flashcard"""
    return f"""
        QTextEdit {{
            font-size: 20px;
            color: {get_text_color()};
            background-color: transparent;
            border: none;
            padding: 0;
            margin: 0;
        }}
    """


def get_delete_button_style():
    """Stile per il pulsante elimina"""
    return """
        QPushButton {
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 4px;
        }
        QPushButton:hover {
            background-color: #EF444430;
        }
    """
