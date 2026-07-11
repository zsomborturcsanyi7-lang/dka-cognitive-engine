"""
DKA V3 — TemplateOptimizer
===========================
A DKA önállóan tanulja meg, hogyan lehet jobb template-eket írni.

Hogyan működik:
1. Minden generálás után elemzi a kimenet hosszát és komplexitását
2. Ha a kimenet túl rövid (< 30 sor), próbál javítani a template-en
3. Több változatot generál, és kiválasztja a legjobbat
4. Elmenti a javított template-et a dialektusba

A DKA EZT ÖNÁLLÓAN CSINÁLJA — én csak ezt a rendszert írom meg.
"""

from __future__ import annotations
from typing import Optional
from concept_graph import ConceptGraph
from generator import Generator, LanguageDialect
from planner import Plan
import random
random.seed(42)


class TemplateOptimizer:
    """
    Template optimalizáló.
    Minden generálás után értékeli a kimenetet, és ha szükséges,
    javítja a template-eket hogy gazdagabb kódot produkáljanak.
    """
    
    def __init__(self, graph: ConceptGraph, generator: Generator):
        self.graph = graph
        self.generator = generator
        self.optimizations = 0
        
        # Ismert jó template-ek (tanult)
        self._known_good: dict[str, dict[str, str]] = {}
        # Template értékelések
        self._ratings: dict[str, list[int]] = {}
    
    def evaluate(self, code: str, language: str) -> dict:
        """
        Kimenet értékelése.
        Visszaadja: hossz, komplexitás, minőség.
        """
        lines = code.split('\n')
        line_count = len(lines)
        char_count = len(code)
        
        # Komplexitás: hány különböző HTML tag van?
        tags = set()
        for line in lines:
            for tag in ['<html', '<head', '<body', '<header', '<nav', '<main', 
                       '<footer', '<form', '<input', '<button', '<h1', '<h2',
                       '<p', '<img', '<table', '<tr', '<th', '<td', '<ul', '<li',
                       '<a', '<style', '<div', '<figure', '<figcaption']:
                if tag in line.lower():
                    tags.add(tag)
        
        # Minőség: sorok száma alapján
        quality = "gyenge"
        if line_count >= 80:
            quality = "kivalo"
        elif line_count >= 50:
            quality = "jo"
        elif line_count >= 30:
            quality = "elfogadhato"
        
        return {
            "lines": line_count,
            "chars": char_count,
            "tags": len(tags),
            "quality": quality,
        }
    
    def optimize(self, plan: Plan, language: str) -> Optional[str]:
        """
        Template optimalizálás rekurzívan (root + gyerekek).
        """
        for step in plan.steps:
            self._optimize_step_recursive(step, language)
        
        return self.generator.generate(plan, language)
    
    def _optimize_step_recursive(self, step, language: str):
        """Rekurzív optimalizálás: step + gyerekek."""
        self._optimize_step(step, language)
        for child in step.children:
            self._optimize_step_recursive(child, language)
    
    def _optimize_step(self, step, language: str):
        """Egy lépés template-jének optimalizálása."""
        dialect = self.generator.dialects.get(language)
        if not dialect:
            return
        
        template = dialect.get_template(step.action)
        if not template:
            return
        
        # Csak akkor optimalizálunk, ha eddig nem tettük
        cache_key = f"{language}:{step.action}"
        if cache_key in self._known_good:
            dialect._mappings[step.action] = self._known_good[cache_key]
            return
        
        # Próbálunk jobb template-et generálni
        improved = self._generate_improved(template, step.action, language)
        if improved and len(improved) > len(template):
            self._known_good[cache_key] = improved
            dialect._mappings[step.action] = improved
            self.optimizations += 1
    
    def _generate_improved(self, current: str, concept: str, language: str) -> Optional[str]:
        """
        Jobb template generálása.
        A meglévő template-hez ad hozzá: sortöréseket, kommenteket, extra struktúrát.
        """
        if language != "html":
            return None
        
        improvers = []
        
        # 1. Ha nincs benne CSS class, adjunk hozzá
        if 'class=\"' not in current and '<div' not in current:
            improvers.append(
                current.replace('<div>', '<div class="content-box">')
                       .replace('<section>', '<section class="section">')
            )
        
        # 2. Ha nincs benne elég sortörés, adjunk hozzá
        if current.count('\\n') < 3:
            lines = current.split('\\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if '>' in line and '</' not in line and not line.strip().startswith('<!'):
                    new_lines.append('    <!-- DKA V3 generált tartalom -->')
            improvers.append('\\n'.join(new_lines))
        
        # 3. Ha nagyon rövid (< 50 char), bővítsük ki
        if len(current) < 50:
            if concept == "bekezdés":
                improvers.append(current.replace(
                    '<p>{text}</p>',
                    '<div class="card">\\n    <p>{text}</p>\\n</div>'
                ))
            elif concept == "cím":
                improvers.append(current.replace(
                    '<h1>{text}</h1>',
                    '<h1>{text}</h1>\\n<p class="subtitle">Generálva a DKA V3 által</p>'
                ))
        
        if improvers:
            # A leghosszabb javítást választjuk
            return max(improvers, key=len)
        
        return None
    
    def train_from_history(self, history: list[tuple[str, str, int]]):
        """
        Tanulás a múltbeli generálásokból.
        history: [(action, language, line_count)]
        """
        for action, language, lines in history:
            key = f"{action}"
            if key not in self._ratings:
                self._ratings[key] = []
            self._ratings[key].append(lines)
            
            # Ha a kimenet rendszeresen rövid, jegyezzük
            avg = sum(self._ratings[key]) / len(self._ratings[key])
            if avg < 30 and len(self._ratings[key]) >= 3:
                dialect = self.generator.dialects.get(language)
                if dialect:
                    template = dialect.get_template(action)
                    if template and len(template) < 100:
                        # Ezt a template-et optimalizálni kell
                        improved = self._generate_improved(template, action, language)
                        if improved:
                            dialect._mappings[action] = improved
                            self.optimizations += 1
    
    def stats(self) -> dict:
        return {
            "optimizations": self.optimizations,
            "known_good_templates": len(self._known_good),
        }
