import os
from pathlib import Path
from PyPDF2 import PdfReader
from typing import Optional

class FileService:
    """Servizio per gestire i file e estrarre il contenuto"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """Estrae il testo da un file PDF"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Errore nell'estrazione del PDF: {e}")
    
    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """Estrae il testo da un file TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Prova con latin-1 se utf-8 fallisce
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                raise Exception(f"Errore nella lettura del file: {e}")
        except Exception as e:
            raise Exception(f"Errore nella lettura del file: {e}")
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Estrae il testo dal file in base all'estensione"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            return FileService.extract_text_from_pdf(file_path)
        elif ext == '.txt':
            return FileService.extract_text_from_txt(file_path)
        else:
            raise Exception(f"Tipo di file non supportato: {ext}")
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Restituisce la dimensione del file in bytes"""
        return os.path.getsize(file_path)
    
    @staticmethod
    def get_file_type(file_path: str) -> str:
        """Restituisce il tipo MIME del file"""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    @staticmethod
    def format_file_size(bytes_size: int) -> str:
        """Formatta la dimensione del file in formato leggibile"""
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f} KB"
        else:
            return f"{bytes_size / (1024 * 1024):.1f} MB"