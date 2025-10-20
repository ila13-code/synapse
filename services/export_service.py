import csv
from typing import List, Dict
from pathlib import Path

class ExportService:
    """Servizio per esportare flashcard in vari formati"""
    
    @staticmethod
    def export_to_csv(flashcards: List[Dict], file_path: str, delimiter: str = ','):
        """Esporta flashcard in formato CSV"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=delimiter)
                
                # Header
                writer.writerow(['Domanda', 'Risposta', 'Difficoltà'])
                
                # Dati
                for card in flashcards:
                    writer.writerow([
                        card['front'],
                        card['back'],
                        card.get('difficulty', 'medium')
                    ])
            
            return True
        except Exception as e:
            raise Exception(f"Errore nell'esportazione CSV: {e}")
    
    @staticmethod
    def export_to_tsv(flashcards: List[Dict], file_path: str):
        """Esporta flashcard in formato TSV (Tab-Separated Values)"""
        return ExportService.export_to_csv(flashcards, file_path, delimiter='\t')
    
    @staticmethod
    def get_export_filter(format_type: str) -> str:
        """Restituisce il filtro per il dialog di salvataggio"""
        if format_type == 'csv':
            return "CSV Files (*.csv)"
        elif format_type == 'tsv':
            return "TSV Files (*.tsv)"
        else:
            return "All Files (*.*)"