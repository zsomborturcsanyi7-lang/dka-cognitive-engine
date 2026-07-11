"""
DKA V3 — SelfImprover
======================
Az önjavító réteg. Tanul a hibákból.

Folyamat:
1. Kap egy feladatot és a generált kódot
2. Ellenőrzi a kimenetet (fordítási hibák, hiányzó elemek)
3. Diagnosztizálja a hibát: mi hiányzik, mi rossz
4. Javítja a ConceptGraph-ot (új fogalom, új kapcsolat, erősebb kapcsolat)
5. Újra generálja a kódot a javított tudással

Ez az a réteg, ami a DKA-t "önszerveződővé" teszi.
Nem kell kézzel betanítani — a hibákból tanul.
"""

from __future__ import annotations
from typing import Optional
from concept_graph import ConceptGraph, Concept, Operation, Property, RelationType, ConceptRelation
from planner import Planner, Plan
from generator import Generator


class SelfImprover:
    """
    Önjavító motor.
    
    Minden generálás után:
    1. Ellenőrzi a kódot (syntax check, struktúra ellenőrzés)
    2. Ha hiba van, diagnosztizálja
    3. Javítja a ConceptGraph-ot
    4. Újra generál
    """
    
    def __init__(self, graph: ConceptGraph, planner: Planner, generator: Generator):
        self.graph = graph
        self.planner = planner
        self.generator = generator
        self.improvement_count = 0
        self.error_log: list[dict] = []
    
    def run(self, goal: str, language: str = "python", 
            max_attempts: int = 3) -> tuple[Optional[str], list[str]]:
        """
        Teljes ciklus: tervez → generál → ellenőriz → javít → újra.
        
        Visszaadja: (végső kód, javítási napló)
        """
        log = []
        
        for attempt in range(1, max_attempts + 1):
            log.append(f"[{attempt}/{max_attempts}] Tervezés: '{goal}'")
            
            # 1. Tervezés
            plan = self.planner.plan(goal)
            if not plan:
                log.append(f"  HIBA: Nem sikerült tervet készíteni")
                # Tanulás: hiányzó fogalmak keresése
                self._learn_from_failed_plan(goal)
                continue
            
            log.append(f"  Terv: {', '.join(s.action for s in plan.steps)} lépés")
            
            # 2. Generálás
            code = self.generator.generate(plan, language)
            if not code:
                log.append(f"  HIBA: Nem sikerült kódot generálni")
                self._learn_from_failed_generation(plan, language)
                continue
            
            # 3. Ellenőrzés
            issues = self._validate_code(code, language)
            
            if not issues:
                log.append(f"  OK: Kód generálva ({len(code)} char)")
                self.improvement_count += 1
                return code, log
            
            # 4. Hiba diagnózis és javítás
            log.append(f"  Problémák ({len(issues)}):")
            for issue in issues:
                log.append(f"    - {issue}")
                self._learn_from_error(goal, plan, code, issue, language)
            
            # 5. Ha nem az utolsó próbálkozás, javított tudással újra
            if attempt < max_attempts:
                log.append(f"  Javítás után újrapróbálkozás...")
        
        return None, log
    
    def _validate_code(self, code: str, language: str) -> list[str]:
        """
        Kód ellenőrzése. Nyelvspecifikus validáció.
        Visszaadja a problémák listáját (üres = nincs hiba).
        """
        issues = []
        
        if language == "python":
            # Python szintaxis ellenőrzés
            try:
                compile(code, '<dka_check>', 'exec')
            except SyntaxError as e:
                issues.append(f"Szintaxis hiba: {e.msg} (sor {e.lineno})")
            except Exception as e:
                issues.append(f"Fordítási hiba: {e}")
            
            # Struktúra ellenőrzés
            if "import" not in code and any(kw in code for kw in ["random.", "json.", "csv."]):
                issues.append("Hiányzó import: a kód használ modult, de nincs import")
            
            # Visszatérési érték ellenőrzés (ha van return, legyen érték is)
            if "return" in code and "return " not in code:
                issues.append("Üres return utasítás")
        
        elif language == "html":
            # HTML struktúra ellenőrzés
            code_upper = code.upper()
            if "<!DOCTYPE HTML>" not in code_upper:
                issues.append("Hiányzó DOCTYPE deklaráció")
            if "<HTML" not in code_upper:
                issues.append("Hiányzó <html> tag")
            if "</HTML>" not in code_upper:
                issues.append("Hiányzó </html> záró tag")
            if "<BODY" not in code_upper:
                issues.append("Hiányzó <body> tag")
        
        return issues
    
    def _learn_from_failed_plan(self, goal: str):
        """Ha nem sikerült tervet készíteni, tanulunk belőle."""
        # Keressünk ismeretlen szavakat a feladatban
        goal_words = goal.lower().split()
        for word in goal_words:
            if word not in self.graph.concepts and len(word) > 3:
                # Ismeretlen fogalom → felvesszük alapszinten
                concept = Concept(
                    name=word,
                    description=f"Ismeretlen fogalom a '{goal}' feladatból",
                    confidence=0.3,  # Alacsony biztonság
                )
                self.graph.add(concept)
                self.error_log.append({
                    "type": "new_concept",
                    "concept": word,
                    "source": goal,
                })
    
    def _learn_from_failed_generation(self, plan: Plan, language: str):
        """Ha a tervből nem sikerült kódot generálni."""
        for step in plan.steps:
            # Hiányzó template a dialektusban
            dialect = self.generator.dialects.get(language)
            if dialect and not dialect.get_template(step.action):
                # Automatikus template generálás: action neve → egyszerű template
                fallback = f"<!-- {step.action} -->"
                dialect.map(step.action, fallback)
                self.error_log.append({
                    "type": "new_template",
                    "action": step.action,
                    "language": language,
                    "template": fallback,
                })
    
    def _learn_from_error(self, goal: str, plan: Plan, code: str,
                          error: str, language: str):
        """Egy hibából tanulás: a hiba típusa alapján javítja a tudást."""
        
        error_lower = error.lower()
        
        # Hiányzó elemek
        if "hiányzó" in error_lower or "missing" in error_lower:
            # Kivonjuk, hogy mi hiányzik
            for word in error.split():
                if word not in self.graph.concepts and len(word) > 3:
                    # Lehet, hogy ez egy hiányzó fogalom
                    concept = Concept(
                        name=word,
                        description=f"Hiányzó elem, amit a '{goal}' feladat igényel",
                        confidence=0.5,
                    )
                    self.graph.add(concept)
        
        # Szintaxis hiba
        if "szintaxis" in error_lower or "syntax" in error_lower:
            # A generátor template-je hibás lehet
            for step in plan.steps:
                concept = self.graph.get(step.action)
                if concept:
                    # Csökkentjük a konfidenciát → másképp kell kezelni
                    concept.confidence = max(0.1, concept.confidence - 0.2)
                    self.error_log.append({
                        "type": "confidence_reduced",
                        "concept": step.action,
                        "new_confidence": concept.confidence,
                    })
        
        # Import hiba
        if "import" in error_lower:
            # A nyelv dialektusához hozzá kell adni az importot
            dialect = self.generator.dialects.get(language)
            if dialect:
                # Keressük, melyik lépés használ külső modult
                for step in plan.steps:
                    action = step.action
                    existing = dialect.get_import(action)
                    if not existing:
                        # Próbáljuk automatikusan
                        import_map = {
                            "véletlen": "import random",
                            "random": "import random",
                            "fájl": "import os",
                            "json": "import json",
                            "csv": "import csv",
                        }
                        for keyword, imp in import_map.items():
                            if keyword in action.lower() or keyword in goal.lower():
                                dialect.map(action, dialect.get_template(action) or f"#{action}", imp)
                                self.error_log.append({
                                    "type": "import_added",
                                    "action": action,
                                    "import": imp,
                                })
                                break
    
    def stats(self) -> dict:
        """Statisztika a tanulásról."""
        return {
            "improvements": self.improvement_count,
            "errors_logged": len(self.error_log),
            "graph_concepts": len(self.graph.concepts),
        }
    
    def report(self) -> str:
        """Tanulási jelentés."""
        lines = ["=== ÖNJAVÍTÓ JELENTÉS ==="]
        lines.append(f"Javítások: {self.improvement_count}")
        lines.append(f"Naplózott hibák: {len(self.error_log)}")
        
        # Hibák típus szerint
        type_counts = {}
        for entry in self.error_log:
            t = entry.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        if type_counts:
            lines.append("Hiba típusok:")
            for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  {t}: {c}")
        
        return "\n".join(lines)
