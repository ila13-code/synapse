

create una copia del file .env.example

rinominatelo semplicemente in .env

mettete la vostra api key di gemini e/o il nome del modello locale che usate

dovrebbe funzionare anche con ollama se usa le api di openai, nel dubbio io sto usando LM-studio e lo consiglio anche a voi perchè non è da linea di comando, ha una gui facile da impostare e gestire tutti i parametri, puoi scaricare tutti i modelli, puoi anche mandargli foto ecc. insomma, è meglio

ma di base useremo gemini-2.5-flash che è molto meglio e gratis


poi eseguire

```python -m venv .venv```
```source .venv/bin/activate && pip install -r requirements.txt```
```py main.py```

