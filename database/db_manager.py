import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "synapse.db"):
        self.db_path = db_path
        self.conn = None
        
    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#8B5CF6',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabella documents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                file_path TEXT,
                file_type TEXT,
                content TEXT,
                size_bytes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabella flashcards
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                difficulty TEXT CHECK(difficulty IN ('easy', 'medium', 'hard')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            )
        ''')
        
        
        # Tabella settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Inserisci impostazioni di default se non esistono
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'light')")
        
        conn.commit()
    
    # --- SUBJECTS ---
    
    def create_subject(self, name: str, description: str = None, color: str = '#8B5CF6') -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO subjects (name, description, color) VALUES (?, ?, ?)',
            (name, description, color)
        )
        conn.commit()
        return cursor.lastrowid
    
    def get_all_subjects(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM subjects ORDER BY created_at DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_subject(self, subject_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_subject(self, subject_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
        conn.commit()
    
    # --- DOCUMENTS ---
    
    def create_document(self, subject_id: int, name: str, file_path: str = None, 
                       file_type: str = None, content: str = None, size_bytes: int = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documents (subject_id, name, file_path, file_type, content, size_bytes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (subject_id, name, file_path, file_type, content, size_bytes))
        conn.commit()
        return cursor.lastrowid
    
    def get_documents_by_subject(self, subject_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM documents WHERE subject_id = ? ORDER BY created_at DESC',
            (subject_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_document(self, document_id: int) -> Dict:
        """Ottiene un singolo documento dal suo ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE id = ?', (document_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def delete_document(self, document_id: int, delete_physical_file: bool = False):
        """
        Elimina un documento dal database
        
        Args:
            document_id: ID del documento da eliminare
            delete_physical_file: Se True, elimina anche il file fisico dal disco
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Se richiesto, elimina anche il file fisico
        if delete_physical_file:
            cursor.execute('SELECT file_path FROM documents WHERE id = ?', (document_id,))
            row = cursor.fetchone()
            
            if row and row['file_path']:
                file_path = row['file_path']
                try:
                    import os
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Errore eliminazione file fisico: {e}")
        
        # Elimina il record dal database
        cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
        conn.commit()
        return True
    
    def get_document_count(self, subject_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM documents WHERE subject_id = ?', (subject_id,))
        return cursor.fetchone()['count']
    
    # --- FLASHCARDS ---
    
    def create_flashcard(self, subject_id: int, front: str, back: str, difficulty: str = 'medium') -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO flashcards (subject_id, front, back, difficulty)
            VALUES (?, ?, ?, ?)
        ''', (subject_id, front, back, difficulty))
        conn.commit()
        return cursor.lastrowid
    
    def create_flashcards_bulk(self, flashcards: List[Dict]):
        """Crea multiple flashcard in una transazione"""
        conn = self.get_connection()
        cursor = conn.cursor()
        for fc in flashcards:
            cursor.execute('''
                INSERT INTO flashcards (subject_id, front, back, difficulty)
                VALUES (?, ?, ?, ?)
            ''', (fc['subject_id'], fc['front'], fc['back'], fc['difficulty']))
        conn.commit()
    
    def get_flashcards_by_subject(self, subject_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM flashcards WHERE subject_id = ? ORDER BY created_at DESC',
            (subject_id,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def update_flashcard(self, flashcard_id: int, front: str, back: str, difficulty: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE flashcards 
            SET front = ?, back = ?, difficulty = ?
            WHERE id = ?
        ''', (front, back, difficulty, flashcard_id))
        conn.commit()
    
    def delete_flashcard(self, flashcard_id: int):
        """Elimina una flashcard dal database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM flashcards WHERE id = ?', (flashcard_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Errore durante l'eliminazione della flashcard: {e}")
            raise e
    
    def get_flashcard_count(self, subject_id: int) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM flashcards WHERE subject_id = ?', (subject_id,))
        return cursor.fetchone()['count']
    
    
    # --- SETTINGS ---
    
    def get_setting(self, key: str, default: str = None) -> str:
        """Ottiene una impostazione dal database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else default
    
    def set_setting(self, key: str, value: str):
        """Salva una impostazione nel database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
        conn.commit()
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None