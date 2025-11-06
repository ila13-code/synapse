import csv
from typing import List, Dict
from pathlib import Path
import zipfile
import json
import os
import tempfile

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
        elif format_type == 'apkg':
            return "Anki Package (*.apkg)"
        else:
            return "All Files (*.*)"
    
    @staticmethod
    def export_to_apkg(flashcards: List[Dict], file_path: str, deck_name: str = "Default"):
        """Esporta flashcard in formato APKG (Anki Package)
        
        Args:
            flashcards: Lista di flashcard da esportare
            file_path: Percorso del file .apkg da creare
            deck_name: Nome del deck Anki (corrisponde esattamente al nome della materia)
        """
        try:
            # Crea una directory temporanea
            with tempfile.TemporaryDirectory() as tmpdir:
                # Crea il file collection.anki2 (database SQLite)
                import sqlite3
                db_path = os.path.join(tmpdir, 'collection.anki2')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Crea le tabelle necessarie (versione semplificata)
                cursor.execute('''
                    CREATE TABLE col (
                        id INTEGER PRIMARY KEY,
                        crt INTEGER NOT NULL,
                        mod INTEGER NOT NULL,
                        scm INTEGER NOT NULL,
                        ver INTEGER NOT NULL,
                        dty INTEGER NOT NULL,
                        usn INTEGER NOT NULL,
                        ls INTEGER NOT NULL,
                        conf TEXT NOT NULL,
                        models TEXT NOT NULL,
                        decks TEXT NOT NULL,
                        dconf TEXT NOT NULL,
                        tags TEXT NOT NULL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE notes (
                        id INTEGER PRIMARY KEY,
                        guid TEXT NOT NULL,
                        mid INTEGER NOT NULL,
                        mod INTEGER NOT NULL,
                        usn INTEGER NOT NULL,
                        tags TEXT NOT NULL,
                        flds TEXT NOT NULL,
                        sfld TEXT NOT NULL,
                        csum INTEGER NOT NULL,
                        flags INTEGER NOT NULL,
                        data TEXT NOT NULL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE cards (
                        id INTEGER PRIMARY KEY,
                        nid INTEGER NOT NULL,
                        did INTEGER NOT NULL,
                        ord INTEGER NOT NULL,
                        mod INTEGER NOT NULL,
                        usn INTEGER NOT NULL,
                        type INTEGER NOT NULL,
                        queue INTEGER NOT NULL,
                        due INTEGER NOT NULL,
                        ivl INTEGER NOT NULL,
                        factor INTEGER NOT NULL,
                        reps INTEGER NOT NULL,
                        lapses INTEGER NOT NULL,
                        left INTEGER NOT NULL,
                        odue INTEGER NOT NULL,
                        odid INTEGER NOT NULL,
                        flags INTEGER NOT NULL,
                        data TEXT NOT NULL
                    )
                ''')
                
                # Crea la tabella graves (richiesta da Anki per le card eliminate)
                cursor.execute('''
                    CREATE TABLE graves (
                        usn INTEGER NOT NULL,
                        oid INTEGER NOT NULL,
                        type INTEGER NOT NULL
                    )
                ''')
                
                # Crea la tabella revlog (log delle revisioni)
                cursor.execute('''
                    CREATE TABLE revlog (
                        id INTEGER PRIMARY KEY,
                        cid INTEGER NOT NULL,
                        usn INTEGER NOT NULL,
                        ease INTEGER NOT NULL,
                        ivl INTEGER NOT NULL,
                        lastIvl INTEGER NOT NULL,
                        factor INTEGER NOT NULL,
                        time INTEGER NOT NULL,
                        type INTEGER NOT NULL
                    )
                ''')
                
                import time
                timestamp = int(time.time())
                
                # Modello base per flashcard - completo di tutti i campi richiesti da Anki
                models = {
                    "1": {
                        "id": 1,
                        "name": "Basic",
                        "type": 0,
                        "mod": timestamp,
                        "usn": -1,
                        "sortf": 0,
                        "did": 1,
                        "tmpls": [
                            {
                                "name": "Card 1",
                                "ord": 0,
                                "qfmt": "{{Front}}",
                                "afmt": "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}",
                                "did": None,
                                "bqfmt": "",
                                "bafmt": ""
                            }
                        ],
                        "flds": [
                            {
                                "name": "Front",
                                "ord": 0,
                                "sticky": False,
                                "rtl": False,
                                "font": "Arial",
                                "size": 20,
                                "description": "",
                                "plainText": False,
                                "collapsed": False,
                                "excludeFromSearch": False
                            },
                            {
                                "name": "Back",
                                "ord": 1,
                                "sticky": False,
                                "rtl": False,
                                "font": "Arial",
                                "size": 20,
                                "description": "",
                                "plainText": False,
                                "collapsed": False,
                                "excludeFromSearch": False
                            }
                        ],
                        "css": ".card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n",
                        "latexPre": "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage[utf8]{inputenc}\n\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n",
                        "latexPost": "\\end{document}",
                        "latexsvg": False,
                        "req": [[0, "all", [0]]]
                    }
                }
                
                decks = {
                    "1": {
                        "id": 1,
                        "name": deck_name,  # Usa il nome del deck passato come parametro
                        "mod": timestamp,
                        "usn": -1,
                        "lrnToday": [0, 0],
                        "revToday": [0, 0],
                        "newToday": [0, 0],
                        "timeToday": [0, 0],
                        "collapsed": False,
                        "browserCollapsed": False,
                        "desc": "",
                        "dyn": 0,
                        "conf": 1,
                        "extendNew": 10,
                        "extendRev": 50
                    }
                }
                
                # Inserisci la collezione
                cursor.execute('''
                    INSERT INTO col VALUES (
                        1, ?, ?, 0, 11, 0, 0, 0, '{}', ?, ?, '{}', '{}'
                    )
                ''', (timestamp, timestamp, json.dumps(models), json.dumps(decks)))
                
                # Inserisci le flashcard come note e card
                for i, card in enumerate(flashcards):
                    note_id = i + 1
                    card_id = i + 1
                    
                    # Genera un GUID unico
                    import hashlib
                    guid = hashlib.md5(f"{card['front']}{card['back']}{i}".encode()).hexdigest()[:10]
                    
                    # Campi della nota (Front e Back separati da \x1f)
                    flds = f"{card['front']}\x1f{card['back']}"
                    
                    # Inserisci la nota
                    cursor.execute('''
                        INSERT INTO notes VALUES (
                            ?, ?, 1, ?, 0, '', ?, ?, 0, 0, ''
                        )
                    ''', (note_id, guid, timestamp, flds, card['front']))
                    
                    # Inserisci la card
                    cursor.execute('''
                        INSERT INTO cards VALUES (
                            ?, ?, 1, 0, ?, 0, 0, 0, ?, 0, 2500, 0, 0, 0, 0, 0, 0, ''
                        )
                    ''', (card_id, note_id, timestamp, i + 1))
                
                conn.commit()
                conn.close()
                
                # Crea il file media (vuoto per ora)
                media_path = os.path.join(tmpdir, 'media')
                with open(media_path, 'w') as f:
                    f.write('{}')
                
                # Crea il file .apkg (zip contenente collection.anki2 e media)
                with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(db_path, 'collection.anki2')
                    zipf.write(media_path, 'media')
            
            return True
        except Exception as e:
            raise Exception(f"Errore nell'esportazione APKG: {e}")