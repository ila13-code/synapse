"""
Carica le variabili d'ambiente dal file .env se esiste
"""
import os
from pathlib import Path

def load_env():
    """Carica le variabili d'ambiente dal file .env"""
    env_file = Path('.env')
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()