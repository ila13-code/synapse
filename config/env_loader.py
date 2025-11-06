"""
Carica le variabili d'ambiente dal file .env se esiste
"""
import os
from pathlib import Path

def load_env():
    """Carica le variabili d'ambiente dal file .env"""
    env_file = Path('.env')
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Ottiene un valore booleano dall'ambiente.
    
    Valori accettati per True: 'true', 'yes', '1', 'on' (case-insensitive)
    Valori accettati per False: 'false', 'no', '0', 'off' (case-insensitive)
    
    Args:
        key: Nome della variabile d'ambiente
        default: Valore di default se la variabile non esiste
        
    Returns:
        bool: Valore booleano
    """
    value = os.environ.get(key, '').lower()
    if value in ('true', 'yes', '1', 'on'):
        return True
    elif value in ('false', 'no', '0', 'off'):
        return False
    return default