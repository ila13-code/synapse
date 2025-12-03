import re
from typing import Dict, List, Optional
from functools import lru_cache

try:
    from pylatexenc.latex2text import LatexNodes2Text
    PYLATEXENC_AVAILABLE = True
except ImportError:
    PYLATEXENC_AVAILABLE = False
    print("⚠️  pylatexenc non disponibile. Usando conversione fallback.")
    print("   Per migliori risultati: pip install pylatexenc")


class LaTeXService:
    """Servizio per processare e convertire formule LaTeX nelle flashcard"""
    
    # Pattern per rilevare LaTeX inline e block
    LATEX_INLINE_PATTERN = re.compile(r'\$(?!\$)(.*?)\$(?!\$)', re.DOTALL)
    LATEX_BLOCK_PATTERN = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    
    # Pattern alternativi per LaTeX (es. \( ... \) e \[ ... \])
    LATEX_INLINE_ALT_PATTERN = re.compile(r'\\\((.*?)\\\)', re.DOTALL)
    LATEX_BLOCK_ALT_PATTERN = re.compile(r'\\\[(.*?)\\\]', re.DOTALL)
    
    # Configurazione converter (singleton)
    _converter: Optional[LatexNodes2Text] = None
    
    @classmethod
    def get_converter(cls) -> Optional[LatexNodes2Text]:
        """Restituisce il converter LaTeX (singleton pattern)"""
        if cls._converter is None and PYLATEXENC_AVAILABLE:
            cls._converter = LatexNodes2Text(
                # Opzioni di conversione
                strict_latex_spaces=False,  # Più permissivo con spazi
                keep_braced_groups=False,   # Rimuovi graffe inutili
                keep_comments=False         # Ignora commenti LaTeX
            )
        return cls._converter
    
    @staticmethod
    def has_latex(text: str) -> bool:
        """Verifica se il testo contiene formule LaTeX"""
        if not text:
            return False
        return bool(
            LaTeXService.LATEX_INLINE_PATTERN.search(text) or 
            LaTeXService.LATEX_BLOCK_PATTERN.search(text) or
            LaTeXService.LATEX_INLINE_ALT_PATTERN.search(text) or
            LaTeXService.LATEX_BLOCK_ALT_PATTERN.search(text)
        )
    
    @staticmethod
    @lru_cache(maxsize=512)  # Cache aumentata per più flashcard
    def convert_latex_to_unicode(latex_content: str) -> str:
        """
        Converte formule LaTeX in Unicode usando pylatexenc.
        Usa cache per performance su formule ripetute.
        
        Args:
            latex_content: Contenuto LaTeX da convertire (senza delimitatori)
        
        Returns:
            Testo convertito in formato Unicode
        """
        if not latex_content.strip():
            return latex_content
        
        converter = LaTeXService.get_converter()
        
        if converter and PYLATEXENC_AVAILABLE:
            try:
                # Conversione con pylatexenc
                result = converter.latex_to_text(latex_content)
                return result.strip()
            except Exception as e:
                # Fallback silenzioso alla conversione manuale
                return LaTeXService._convert_latex_fallback(latex_content)
        else:
            # Fallback se pylatexenc non disponibile
            return LaTeXService._convert_latex_fallback(latex_content)
    
    @staticmethod
    def _convert_latex_fallback(latex_content: str) -> str:
        """
        Fallback per conversione LaTeX manuale (versione semplificata).
        Usato quando pylatexenc non è disponibile.
        """
        result = latex_content.strip()
        
        # Conversioni base
        conversions = {
            # Lettere greche minuscole
            r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
            r'\epsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ',
            r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
            r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
            r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ',
            r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
            
            # Lettere greche maiuscole
            r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
            r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Phi': 'Φ',
            r'\Psi': 'Ψ', r'\Omega': 'Ω',
            
            # Operatori matematici
            r'\times': '×', r'\div': '÷', r'\pm': '±', r'\mp': '∓',
            r'\cdot': '·', r'\leq': '≤', r'\geq': '≥', r'\neq': '≠',
            r'\approx': '≈', r'\equiv': '≡', r'\propto': '∝',
            r'\infty': '∞', r'\partial': '∂', r'\nabla': '∇',
            r'\sum': '∑', r'\prod': '∏', r'\int': '∫', r'\oint': '∮',
            
            # Insiemi e logica
            r'\in': '∈', r'\notin': '∉', r'\subset': '⊂', r'\subseteq': '⊆',
            r'\supset': '⊃', r'\supseteq': '⊇', r'\cup': '∪', r'\cap': '∩',
            r'\emptyset': '∅', r'\forall': '∀', r'\exists': '∃',
            r'\neg': '¬', r'\land': '∧', r'\lor': '∨',
            r'\implies': '⇒', r'\iff': '⇔',
            
            # Frecce
            r'\rightarrow': '→', r'\leftarrow': '←', r'\leftrightarrow': '↔',
            r'\Rightarrow': '⇒', r'\Leftarrow': '⇐', r'\Leftrightarrow': '⇔',
            r'\uparrow': '↑', r'\downarrow': '↓',
            
            # Altri simboli
            r'\angle': '∠', r'\degree': '°', r'\perp': '⊥', r'\parallel': '∥',
        }
        
        # Frazioni
        result = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', result)
        
        # Radici \sqrt{...} e \sqrt[n]{...}
        result = re.sub(
            r'\\sqrt(?:\[([^\]]+)\])?\{([^}]+)\}',
            lambda m: f'<sup>{m.group(1)}</sup>√({m.group(2)})' if m.group(1) else f'√({m.group(2)})',
            result
        )
        
        # Esponenti ^{...} o ^x - COMPATIBILE CON HTML
        result = re.sub(
            r'\^(\{[^}]+\}|[a-zA-Z0-9])',
            lambda m: f'<sup>{m.group(1).strip("{}")}</sup>',
            result
        )
        
        # Pedici _{...} o _x - COMPATIBILE CON HTML
        result = re.sub(
            r'_(\{[^}]+\}|[a-zA-Z0-9])',
            lambda m: f'<sub>{m.group(1).strip("{}")}</sub>',
            result
        )
        
        # Simboli LaTeX -> Unicode (ordina per lunghezza decrescente)
        for latex, unicode_char in sorted(conversions.items(), key=lambda x: len(x[0]), reverse=True):
            result = re.sub(re.escape(latex) + r'(?![a-zA-Z])', unicode_char, result)
        
        # Pulisci comandi text
        result = re.sub(r'\\text(?:bf|it|rm|sf)?\{([^}]+)\}', r'\1', result)
        
        # Gestisci \mathbb, \mathcal, \mathbf (rimuovi comando, mantieni contenuto)
        result = re.sub(r'\\math(?:bb|cal|bf|rm|sf|it)\{([^}]+)\}', r'\1', result)
        
        # Pulisci spazi multipli
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result
    
    @staticmethod
    def process_text(text: str) -> str:
        """
        Processa un testo completo, convertendo tutte le formule LaTeX.
        Ottimizzato per Qt QLabel.setHtml()
        
        Args:
            text: Testo che può contenere formule LaTeX
        
        Returns:
            Testo HTML-formatted con formule LaTeX convertite, pronto per setHtml()
        """
        if not text:
            return text
        
        result = text
        
        # Prima converti i blocchi $$ ... $$ (display math - più priorità)
        def replace_block(match):
            latex_content = match.group(1)
            converted = LaTeXService.convert_latex_to_unicode(latex_content)
            
            # Blocco: centra e rendi più visibile
            # Font-size maggiore e bold per formule display
            return (
                f'<div style="text-align: center; margin: 15px 0; '
                f'font-size: 120%; font-weight: bold; line-height: 1.6;">'
                f'{converted}</div>'
            )
        
        result = LaTeXService.LATEX_BLOCK_PATTERN.sub(replace_block, result)
        result = LaTeXService.LATEX_BLOCK_ALT_PATTERN.sub(replace_block, result)
        
        # Poi converti inline $ ... $ (inline math)
        def replace_inline(match):
            latex_content = match.group(1)
            converted = LaTeXService.convert_latex_to_unicode(latex_content)
            
            # Inline: span con stile per distinguere dal testo normale
            # Font leggermente più grande e colore diverso
            return (
                f'<span style="font-style: italic; font-size: 105%; '
                f'color: #2c3e50; font-weight: 500;">{converted}</span>'
            )
        
        result = LaTeXService.LATEX_INLINE_PATTERN.sub(replace_inline, result)
        result = LaTeXService.LATEX_INLINE_ALT_PATTERN.sub(replace_inline, result)
        
        return result
    
    @staticmethod
    def process_flashcard(flashcard: Dict, verbose: bool = False) -> Dict:
        """
        Processa una flashcard, convertendo eventuali formule LaTeX in front e back.
        
        Args:
            flashcard: Dizionario con campi 'front', 'back', ecc.
            verbose: Se True, stampa log di conversione
        
        Returns:
            Flashcard con LaTeX convertito (copia, non modifica l'originale)
        """
        processed = flashcard.copy()
        converted_fields = []
        
        for field in ['front', 'back']:
            if field in processed and LaTeXService.has_latex(processed[field]):
                processed[field] = LaTeXService.process_text(processed[field])
                converted_fields.append(field)
        
        if verbose and converted_fields:
            print(f"[LaTeX] Convertito LaTeX nei campi: {', '.join(converted_fields)}")
        
        return processed
    
    @staticmethod
    def process_flashcards_batch(flashcards: List[Dict], verbose: bool = True) -> List[Dict]:
        """
        Processa un batch di flashcard, convertendo tutte le formule LaTeX.
        
        Args:
            flashcards: Lista di flashcard da processare
            verbose: Se True, stampa statistiche di conversione
        
        Returns:
            Lista di flashcard con LaTeX convertito
        """
        if not flashcards:
            return []
        
        processed = []
        latex_count = 0
        
        for card in flashcards:
            has_latex_in_card = any(
                LaTeXService.has_latex(card.get(field, '')) 
                for field in ['front', 'back']
            )
            
            if has_latex_in_card:
                latex_count += 1
            
            processed.append(LaTeXService.process_flashcard(card, verbose=False))
        
        if verbose and latex_count > 0:
            percentage = (latex_count / len(flashcards) * 100)
            print(f"[LaTeX] Processate {latex_count}/{len(flashcards)} flashcard con LaTeX ({percentage:.1f}%)")
            
            if not PYLATEXENC_AVAILABLE:
                print("💡 Suggerimento: installa pylatexenc per conversioni migliori")
                print("   → pip install pylatexenc")
        
        return processed
    
    @staticmethod
    def clear_cache():
        """Pulisce la cache delle conversioni LaTeX"""
        LaTeXService.convert_latex_to_unicode.cache_clear()
        print("[LaTeX] Cache pulita")
