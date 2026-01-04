"""
Physics Formula Extractor

Detects and converts physics formulas to LaTeX format.
Supports physics-specific formulas including:
- Mechanics: F=ma, KE, PE, momentum, work, power
- Electricity: V=IR, P=VI, Coulomb's law, capacitance
- Magnetism: F=BIL, flux, Ampere's law
- Optics: lens formula, mirror formula, refraction
- Thermodynamics: PV=nRT, heat transfer, entropy
- Modern Physics: E=mc², photoelectric effect, atomic models
- Waves: v=fλ, wave equations, interference
"""

import re
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class PhysicsFormulaExtractor:
    """
    Extract and convert physics formulas to LaTeX
    """
    
    def __init__(self):
        """Initialize the physics formula extractor"""
        
        # Physics-specific symbols and patterns
        self.physics_symbols = {
            # Greek letters
            'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
            'ε': r'\epsilon', 'θ': r'\theta', 'λ': r'\lambda', 'μ': r'\mu',
            'ν': r'\nu', 'ρ': r'\rho', 'σ': r'\sigma', 'τ': r'\tau',
            'φ': r'\phi', 'ψ': r'\psi', 'ω': r'\omega', 'Ω': r'\Omega',
            'Δ': r'\Delta', 'Σ': r'\Sigma',
            
            # Physics quantities
            '∑': r'\sum', '∫': r'\int', '∂': r'\partial',
            '≈': r'\approx', '≠': r'\neq', '≤': r'\leq', '≥': r'\geq',
            '∞': r'\infty', '√': r'\sqrt', '∝': r'\propto',
            '×': r'\times', '÷': r'\div', '·': r'\cdot',
            '°': r'^\circ', '→': r'\rightarrow', '⃗': r'\vec'
        }
        
        # Comprehensive physics formula patterns
        self.formula_patterns = [
            # Mechanics
            (r'F\s*=\s*ma', r'$F = ma$'),  # Newton's 2nd law
            (r'F\s*=\s*m\s*a', r'$F = ma$'),
            (r'KE\s*=\s*½\s*mv²', r'$KE = \frac{1}{2}mv^2$'),
            (r'PE\s*=\s*mgh', r'$PE = mgh$'),
            (r'p\s*=\s*mv', r'$p = mv$'),  # Momentum
            (r'W\s*=\s*F\s*[×·]\s*d', r'$W = F \cdot d$'),  # Work
            (r'P\s*=\s*W/t', r'$P = \frac{W}{t}$'),  # Power
            (r'v²\s*=\s*u²\s*\+\s*2as', r'$v^2 = u^2 + 2as$'),
            (r'v\s*=\s*u\s*\+\s*at', r'$v = u + at$'),
            (r's\s*=\s*ut\s*\+\s*½at²', r'$s = ut + \frac{1}{2}at^2$'),
            
            # Gravitation
            (r'F\s*=\s*G\s*m₁m₂/r²', r'$F = \frac{Gm_1m_2}{r^2}$'),
            (r'g\s*=\s*GM/R²', r'$g = \frac{GM}{R^2}$'),
            (r'F\s*=\s*GMm/r²', r'$F = \frac{GMm}{r^2}$'),
            
            # Rotational Motion
            (r'τ\s*=\s*r\s*[×·]\s*F', r'$\tau = r \times F$'),  # Torque
            (r'L\s*=\s*Iω', r'$L = I\omega$'),  # Angular momentum
            (r'KE\s*=\s*½Iω²', r'$KE = \frac{1}{2}I\omega^2$'),
            
            # Electricity & Magnetism
            (r'V\s*=\s*IR', r'$V = IR$'),  # Ohm's law
            (r'I\s*=\s*V/R', r'$I = \frac{V}{R}$'),
            (r'R\s*=\s*V/I', r'$R = \frac{V}{I}$'),
            (r'P\s*=\s*VI', r'$P = VI$'),  # Power
            (r'P\s*=\s*I²R', r'$P = I^2R$'),
            (r'P\s*=\s*V²/R', r'$P = \frac{V^2}{R}$'),
            (r'Q\s*=\s*It', r'$Q = It$'),  # Charge
            (r'F\s*=\s*k\s*q₁q₂/r²', r'$F = \frac{kq_1q_2}{r^2}$'),  # Coulomb's law
            (r'E\s*=\s*F/q', r'$E = \frac{F}{q}$'),  # Electric field
            (r'C\s*=\s*Q/V', r'$C = \frac{Q}{V}$'),  # Capacitance
            (r'F\s*=\s*BIL', r'$F = BIL$'),  # Magnetic force
            (r'F\s*=\s*qvB', r'$F = qvB$'),  # Lorentz force
            (r'Φ\s*=\s*BA', r'$\Phi = BA$'),  # Magnetic flux
            (r'ε\s*=\s*-dΦ/dt', r'$\varepsilon = -\frac{d\Phi}{dt}$'),  # Faraday's law
            
            # Optics
            (r'1/f\s*=\s*1/v\s*[+-]\s*1/u', r'$\frac{1}{f} = \frac{1}{v} \pm \frac{1}{u}$'),  # Lens formula
            (r'1/v\s*\+\s*1/u\s*=\s*1/f', r'$\frac{1}{v} + \frac{1}{u} = \frac{1}{f}$'),
            (r'n\s*=\s*c/v', r'$n = \frac{c}{v}$'),  # Refractive index
            (r'n₁\s*sin\s*θ₁\s*=\s*n₂\s*sin\s*θ₂', r'$n_1 \sin\theta_1 = n_2 \sin\theta_2$'),  # Snell's law
            (r'm\s*=\s*-v/u', r'$m = -\frac{v}{u}$'),  # Magnification
            (r'm\s*=\s*h₂/h₁', r'$m = \frac{h_2}{h_1}$'),
            
            # Thermodynamics
            (r'PV\s*=\s*nRT', r'$PV = nRT$'),  # Ideal gas law
            (r'Q\s*=\s*mcΔT', r'$Q = mc\Delta T$'),  # Heat transfer
            (r'ΔU\s*=\s*Q\s*-\s*W', r'$\Delta U = Q - W$'),  # First law
            (r'η\s*=\s*W/Q', r'$\eta = \frac{W}{Q}$'),  # Efficiency
            (r'η\s*=\s*1\s*-\s*T₂/T₁', r'$\eta = 1 - \frac{T_2}{T_1}$'),  # Carnot efficiency
            
            # Waves
            (r'v\s*=\s*fλ', r'$v = f\lambda$'),  # Wave equation
            (r'v\s*=\s*f\s*λ', r'$v = f\lambda$'),
            (r'v\s*=\s*√\(T/μ\)', r'$v = \sqrt{\frac{T}{\mu}}$'),  # Wave speed on string
            (r'I\s*∝\s*A²', r'$I \propto A^2$'),  # Intensity
            (r'β\s*=\s*10\s*log₁₀\(I/I₀\)', r'$\beta = 10 \log_{10}\left(\frac{I}{I_0}\right)$'),  # Decibel
            
            # Modern Physics
            (r'E\s*=\s*mc²', r'$E = mc^2$'),  # Einstein's mass-energy
            (r'E\s*=\s*hf', r'$E = hf$'),  # Photon energy
            (r'E\s*=\s*hν', r'$E = h\nu$'),
            (r'λ\s*=\s*h/p', r'$\lambda = \frac{h}{p}$'),  # de Broglie wavelength
            (r'KEmax\s*=\s*hf\s*-\s*φ', r'$KE_{max} = hf - \phi$'),  # Photoelectric effect
            (r'1/λ\s*=\s*R\(1/n₁²\s*-\s*1/n₂²\)', r'$\frac{1}{\lambda} = R\left(\frac{1}{n_1^2} - \frac{1}{n_2^2}\right)$'),  # Rydberg formula
            
            # Nuclear Physics
            (r'N\s*=\s*N₀e^-λt', r'$N = N_0e^{-\lambda t}$'),  # Radioactive decay
            (r't₁/₂\s*=\s*0\.693/λ', r'$t_{1/2} = \frac{0.693}{\lambda}$'),  # Half-life
            
            # General patterns
            (r'(\w+)\s*=\s*([^,\n]{5,50})', self._to_latex_generic),  # Generic equation
            (r'([a-zA-Z][₀-₉]*)\s*/\s*([a-zA-Z][₀-₉]*)', self._to_fraction),  # Fractions
            (r'([a-zA-Z])²', r'$\1^2$'),  # Squares
            (r'([a-zA-Z])³', r'$\1^3$'),  # Cubes
            (r'√([a-zA-Z]+)', r'$\sqrt{\1}$'),  # Square roots
        ]
        
        # Common physics variables
        self.physics_vars = {
            'F': 'Force', 'm': 'mass', 'a': 'acceleration',
            'v': 'velocity', 'u': 'initial velocity', 't': 'time',
            'KE': 'Kinetic Energy', 'PE': 'Potential Energy',
            'p': 'momentum', 'W': 'Work', 'P': 'Power',
            'V': 'Voltage/Volume', 'I': 'Current', 'R': 'Resistance',
            'Q': 'Charge/Heat', 'E': 'Energy/Electric Field',
            'B': 'Magnetic Field', 'C': 'Capacitance',
            'f': 'frequency', 'λ': 'wavelength', 'T': 'Temperature/Tension',
            'n': 'refractive index', 'g': 'gravity', 'h': 'height/Planck constant'
        }
        
        logger.info("Physics Formula Extractor initialized")
    
    def extract_formulas(self, text_blocks: List[Dict]) -> List[Dict]:
        """
        Extract physics formulas from text blocks
        
        Args:
            text_blocks: List of text block dictionaries
        
        Returns:
            List of formula dictionaries with LaTeX
        """
        formulas = []
        
        for block in text_blocks:
            text = block.get('text', '')
            block_formulas = self._find_formulas_in_text(text)
            
            for formula_text, latex in block_formulas:
                formulas.append({
                    'raw_text': formula_text,
                    'latex': latex,
                    'page': block.get('page'),
                    'metadata': block.get('metadata', {})
                })
        
        logger.info(f"   [+] Extracted {len(formulas)} formulas")
        return formulas
    
    def _find_formulas_in_text(self, text: str) -> List[Tuple[str, str]]:
        """Find all formulas in text and convert to LaTeX"""
        formulas = []
        
        for pattern, replacement in self.formula_patterns:
            if callable(replacement):
                # Dynamic pattern processing
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    formula_text = match.group(0)
                    latex = replacement(formula_text)
                    formulas.append((formula_text, latex))
            else:
                # Static pattern replacement
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    formula_text = match.group(0)
                    formulas.append((formula_text, replacement))
        
        return formulas
    
    def _to_latex_generic(self, text: str) -> str:
        """Convert generic equation to LaTeX"""
        # Replace physics symbols
        latex = text
        for symbol, latex_code in self.physics_symbols.items():
            latex = latex.replace(symbol, latex_code)
        
        # Wrap in math mode
        if not latex.startswith('$'):
            latex = f'${latex}$'
        
        return latex
    
    def _to_fraction(self, text: str) -> str:
        """Convert division to LaTeX fraction"""
        match = re.match(r'([a-zA-Z][₀-₉]*)\s*/\s*([a-zA-Z][₀-₉]*)', text)
        if match:
            num, denom = match.groups()
            return f'$\\frac{{{num}}}{{{denom}}}$'
        return text
    
    def convert_to_latex(self, formula_text: str) -> str:
        """
        Convert a physics formula text to LaTeX
        
        Args:
            formula_text: Raw formula text
        
        Returns:
            LaTeX formatted string
        """
        # Try each pattern
        for pattern, replacement in self.formula_patterns:
            if callable(replacement):
                match = re.match(pattern, formula_text, re.IGNORECASE)
                if match:
                    return replacement(formula_text)
            else:
                match = re.match(pattern, formula_text, re.IGNORECASE)
                if match:
                    return replacement
        
        # Default: generic conversion
        return self._to_latex_generic(formula_text)
    
    def is_formula(self, text: str) -> bool:
        """
        Check if text contains a physics formula
        
        Args:
            text: Text to check
        
        Returns:
            True if formula detected
        """
        # Check for physics symbols
        has_symbols = any(symbol in text for symbol in self.physics_symbols.keys())
        
        # Check for equation pattern
        has_equation = bool(re.search(r'[A-Za-z]\s*=\s*', text))
        
        # Check for physics variables
        has_physics_vars = any(var in text for var in self.physics_vars.keys())
        
        return has_symbols or (has_equation and has_physics_vars)
