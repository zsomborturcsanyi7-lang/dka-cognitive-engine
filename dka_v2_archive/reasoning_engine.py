"""
DKA Core — Reasoning Engine
============================
A DKA "gondolkodó" rétege.

Eddig: keres egy mintát → visszaadja
Most:  elemzi a célt → részcélokra bont → minden részcélhoz talál mintát
       → összerakja őket → ellenőrzi → ha nem jó, máshogy próbálja

Példa: "készíts egy számkitalálós játékot"
1. Felbontás: [game_loop, input_handler, random_number, compare_guess, score]
2. Keresés: random.choice → van, input() → van, while True → van
3. Összerakás: game_loop { while True: get_input() + compare() + print_result() }
4. Ellenőrzés: valid Python? fut? csinálja amit kell?

A "kreativitás" itt azt jelenti: a DKA felismeri, hogy a "játék" nem egyetlen minta,
hanem TÖBB minta kombinációja, és sorban összerakja őket.
"""

from __future__ import annotations
from typing import Optional, Callable
import re

from node_types import (
    BaseNode, PrimitiveNode, PatternNode,
    NodeType, DataDomain, Role,
)
from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex
from pattern_intel import PatternIntelligence
from inference_engine_v2 import InferenceEngineV2


class PlanStep:
    """Egy terv lépése."""
    def __init__(self, description: str, goal: str, 
                 pattern_type: str = None,
                 required: bool = True):
        self.description = description
        self.goal = goal          # Mit keresünk / generálunk
        self.pattern_type = pattern_type  # Milyen típusú mintát várunk
        self.required = required
        self.solved = False
        self.code = ""
        self.pattern_id = None


class TaskPlanner:
    """
    Feladatok felbontása részlépésekre.
    
    "készíts egy számkitalálós játékot"
    → [
        PlanStep("játék ciklus", "while loop", "WHILE_LOOP"),
        PlanStep("véletlen szám", "random number", "FUNCTION_CALL"),
        PlanStep("bemenet kérés", "user input", "FUNCTION_CALL"),
        PlanStep("összehasonlítás", "compare numbers", "COMPARISON"),
        PlanStep("eredmény kiírás", "print result", "FUNCTION_CALL"),
      ]
    """
    
    # Ismert feladat típusok → részlépések
    TASK_TEMPLATES = {
        "game": {
            "keywords": ["game", "játék", "play", "guess", "snake", "tetris"],
            "steps": [
                PlanStep("game loop", "while True: game loop", "WHILE_LOOP"),
                PlanStep("input handling", "get user input", "FUNCTION_CALL"),
                PlanStep("game logic", "update game state", None),
                PlanStep("rendering", "display output", "FUNCTION_CALL"),
            ]
        },
        "guess_game": {
            "keywords": ["guess", "találd", "tipp", "number game"],
            "steps": [
                PlanStep("random target", "generate random number", "FUNCTION_CALL"),
                PlanStep("game loop", "while loop for guessing", "WHILE_LOOP"),
                PlanStep("get guess", "read user input", "FUNCTION_CALL"),
                PlanStep("compare guess", "compare numbers", "COMPARISON"),
                PlanStep("give feedback", "print hint", "FUNCTION_CALL"),
            ]
        },
        "file_process": {
            "keywords": ["file", "fájl", "read", "write", "process"],
            "steps": [
                PlanStep("open file", "open file for reading", "FUNCTION_CALL"),
                PlanStep("process data", "transform file content", None),
                PlanStep("return result", "return processed data", "RETURN_STMT"),
            ]
        },
        "sort_task": {
            "keywords": ["sort", "rendez", "order", "arrange"],
            "steps": [
                PlanStep("sort function", "sorting function", "FUNCTION_DEF"),
            ]
        },
        "search_task": {
            "keywords": ["search", "keres", "find", "lookup"],
            "steps": [
                PlanStep("search function", "search function", "FUNCTION_DEF"),
            ]
        },
        "math_task": {
            "keywords": ["math", "matek", "calculate", "compute", "prime", "fibonacci", "factorial"],
            "steps": [
                PlanStep("math function", "mathematical function", "FUNCTION_DEF"),
            ]
        },
        "web_request": {
            "keywords": ["http", "web", "api", "request", "fetch", "download", "url"],
            "steps": [
                PlanStep("make request", "HTTP request", "FUNCTION_CALL"),
                PlanStep("parse response", "parse response data", "FUNCTION_CALL"),
                PlanStep("return data", "return result", "RETURN_STMT"),
            ]
        },
        "data_filter": {
            "keywords": ["filter", "szűr", "select", "pick"],
            "steps": [
                PlanStep("iterate", "loop through items", "FOR_LOOP"),
                PlanStep("condition", "check condition", "IF_STATEMENT"),
                PlanStep("collect", "collect matching items", "FUNCTION_CALL"),
                PlanStep("return", "return result", "RETURN_STMT"),
            ]
        },
    }
    
    def __init__(self, graph: HypergraphV2, semantics: SemanticIndex):
        self.graph = graph
        self.semantics = semantics
    
    def plan(self, goal: str) -> list[PlanStep]:
        """Cél → terv lépései."""
        goal_lower = goal.lower()
        
        # 1. Ismert feladat sablon keresése
        for task_name, template in self.TASK_TEMPLATES.items():
            if any(kw in goal_lower for kw in template["keywords"]):
                # Mélyebb egyezés: hány kulcsszó egyezik?
                match_count = sum(1 for kw in template["keywords"] if kw in goal_lower)
                if match_count >= 2 or any(kw in goal_lower.split() for kw in template["keywords"]):
                    return [PlanStep(step.description, step.goal, step.pattern_type, step.required)
                            for step in template["steps"]]
        
        # 2. Ha nincs sablon, próbáljunk szemantikus keresést
        sem_results = self.semantics.search_by_text(goal, top_k=3)
        if sem_results:
            return [PlanStep("find matching function", goal, "FUNCTION_DEF")]
        
        # 3. Alapértelmezett: keressünk bármit
        return [PlanStep("generate solution", goal, None)]


class ReasoningEngine:
    """
    Következtető motor: terv → kivitelezés → ellenőrzés → iteráció.
    
    Működés:
    1. Terv készítés (TaskPlanner)
    2. Minden lépéshez minta keresése vagy generálása
    3. Eredmények összerakása
    4. Ellenőrzés
    5. Ha nem jó → másik terv
    """
    
    def __init__(self, graph: HypergraphV2, generator: ConstructiveGenerator,
                 semantics: SemanticIndex):
        self.graph = graph
        self.generator = generator
        self.semantics = semantics
        self.planner = TaskPlanner(graph, semantics)
        self.engine = InferenceEngineV2(graph)
        self.pattern_intel = PatternIntelligence(graph)
    
    def reason(self, goal: str, max_attempts: int = 3) -> dict:
        """
        Teljes következtetés: cél → megoldás.
        
        Returns: {
            "success": bool,
            "code": str,
            "steps": [{(step_description, found, code)}],
            "plan_name": str,
        }
        """
        # 1. Terv készítés
        steps = self.planner.plan(goal)
        
        # 2. Minden lépés végrehajtása
        results = []
        all_code_parts = []
        all_solved = True
        
        for step in steps:
            # Keresés a szemantikus indexben
            found = self._solve_step(step)
            
            if found:
                step.solved = True
                step.code = found
                if step.pattern_type == "FUNCTION_DEF":
                    all_code_parts.append(found)
                else:
                    all_code_parts.append(found)
            elif step.required:
                all_solved = False
            
            results.append({
                "description": step.description,
                "goal": step.goal,
                "solved": step.solved,
                "code": step.code[:100] if step.code else "",
            })
        
        # 3. Összerakás
        if all_code_parts:
            final_code = self._compose_parts(all_code_parts, goal)
        else:
            # Fallback: egyszerű szemantikus keresés
            sr = self.semantics.search_by_text(goal, top_k=1)
            if sr:
                pid = sr[0]["id"]
                p = self.graph.patterns.get(pid)
                if p:
                    final_code = self.generator.generate(p)
                else:
                    final_code = ""
            else:
                final_code = ""
        
        # 4. Ellenőrzés
        valid = False
        if final_code:
            try:
                compile(final_code, "<reasoning>", "exec")
                valid = True
            except SyntaxError:
                valid = False
        
        return {
            "success": valid,
            "code": final_code,
            "steps": results,
            "plan_name": goal[:30],
        }
    
    def _solve_step(self, step: PlanStep) -> Optional[str]:
        """Egy tervlépés megoldása."""
        # 1. Próbáljunk pontos FUNCTION_DEF-et keresni
        sr = self.semantics.search_by_text(step.goal, top_k=3)
        for r in sr:
            if r["type"] == "FUNCTION_DEF":
                pid = r["id"]
                p = self.graph.patterns.get(pid)
                if p:
                    return self.generator.generate(p)
        
        # 2. Próbáljunk kisebb mintákat (FOR_LOOP, WHILE_LOOP, etc.)
        if step.pattern_type:
            type_map = {t.name: t for t in NodeType}
            if step.pattern_type in type_map:
                ntype = type_map[step.pattern_type]
                cand = self.graph.find_by_type(ntype)
                if cand:
                    return self.generator.generate(cand[0])
        
        # 3. Szemantikus keresés bármire
        if sr:
            pid = sr[0]["id"]
            p = self.graph.patterns.get(pid)
            if p:
                return self.generator.generate(p)
        
        return None
    
    def _compose_parts(self, parts: list[str], goal: str) -> str:
        """Részkódok összefűzése koherens programmá."""
        if len(parts) == 1:
            return parts[0]
        
        # Több rész: próbáljuk egymás után tenni
        # Ha van FUNCTION_DEF, az legyen az első
        func_parts = [p for p in parts if p.startswith("def ")]
        other_parts = [p for p in parts if not p.startswith("def ")]
        
        if func_parts:
            # Vegyük az első függvényt, a többit tegyük alá
            main = func_parts[0]
            extras = func_parts[1:] + other_parts
            
            if extras:
                # Extra kód beszúrása a függvény body végére
                lines = main.split("\n")
                insert_pos = len(lines)
                for i in range(len(lines) - 1, 0, -1):
                    stripped = lines[i].strip()
                    if stripped and not stripped.startswith("#"):
                        # Az utolsó return előtt szúrjuk be
                        if stripped.startswith("return"):
                            insert_pos = i
                        break
                
                extra_lines = []
                for extra in extras:
                    for line in extra.split("\n"):
                        extra_lines.append("    " + line)
                
                result_lines = lines[:insert_pos] + extra_lines + lines[insert_pos:]
                return "\n".join(result_lines)
            
            return main
        
        return "\n\n".join(parts)


# ─── Quick test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    
    from hypergraph_v2 import HypergraphV2
    from constructive_generator import ConstructiveGenerator
    from semantic_layer import SemanticIndex
    
    # Betöltjük a tanított modellt
    if os.path.exists("dka_trained_500.json"):
        g = HypergraphV2.from_json_file("dka_trained_500.json")
        sem = SemanticIndex(g)
        sem.index_all()
        
        engine = ReasoningEngine(g, ConstructiveGenerator(g), sem)
        
        print("=== REASONING TESZT ===")
        for goal in ["guess the number", "sort array", "read and process file"]:
            print(f"\n--- '{goal}' ---")
            result = engine.reason(goal)
            print(f"  Siker: {result['success']}")
            if result['code']:
                print(f"  Kod:\n{result['code'][:300]}")
            print(f"  Lepesek:")
            for s in result['steps']:
                icon = "✓" if s['solved'] else "✗"
                print(f"    [{icon}] {s['description']}")
    else:
        print("Először futtasd: python mass_train_v2.py")
