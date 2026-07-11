"""
DKA V3 — LLM Bridge
====================
Összeköti az LLM kreativitását a DKA determinisztikus generálásával.

Használat:
  bridge = LLMBridge(dka_graph, dka_parser, dka_generator, dka_planner)
  
  # 1. LLM készít egy strukturált tervet
  llm_plan = {
      "type": "játék",
      "components": ["karakter", "ellenség"],
      "title": "Tűzbirodalom",
      "params": {
          "player_speed": 5,
          "player_size": 50,
          "spawn_rate": 0.02,
          "color_scheme": 0
      },
      "description": "Egy fantasy akciójáték ahol a hős tűzlabdákat kerülget"
  }
  
  # 2. Bridge átalakítja DKA tervvé
  result = bridge.generate(llm_plan)
  # → {"main.py": "...", "enemy.py": "..."}
"""

from __future__ import annotations
from typing import Optional, Any
from concept_graph import ConceptGraph, Concept, RelationType
from planner import Planner, GoalParser, PlanStep, Plan
from generator import Generator


class LLMBridge:
    """Összeköti az LLM strukturált kimenetét a DKA generálásával."""
    
    def __init__(self, graph: ConceptGraph, parser: GoalParser,
                 generator: Generator, planner: Planner):
        self.graph = graph
        self.parser = parser
        self.generator = generator
        self.planner = planner
        self._last_plan: Optional[dict] = None
    
    @staticmethod
    def format_llm_prompt(goal: str, available_types: list[str]) -> str:
        """Összeállítja az LLM prompt-ot a strukturált terv kéréséhez.
        
        Ezt a prompt-ot kell elküldeni az LLM-nek (Hermes agent-en keresztül).
        Az LLM JSON-t ad vissza, amit a generate() vár.
        """
        types_str = ", ".join(available_types)
        return f"""Egy determinisztikus kódgenerátor (DKA) számára készíts strukturált tervet.

Feladat: {goal}

Elérhető komponensek: {types_str}

Válasz CSAK JSON formátumban, semmi más:

{{
    "type": "játék" | "weblap" | "függvény" | "osztály" | "algoritmus",
    "components": ["komponens1", "komponens2", ...],
    "title": "Cím / játék cím",
    "description": "Rövid leírás (10-20 szó)",
    "params": {{
        "player_speed": 5,
        "player_size": 50,
        "spawn_rate": 0.02,
        "color_scheme": 0,
        "theme": "fantasy | sci-fi | horror | kaland"
    }},
    "features": ["extra funkciók"]
}}

Szabályok:
- Csak JSON, semmi magyarázat
- components csak a megadott típusokból választhat
- A params legyen értelmes a témához
- color_scheme: 0-4 között
"""
    
    def generate_from_llm(self, llm_json: dict) -> Optional[dict[str, str] | str]:
        """LLM strukturált JSON-jából generál kódot.
        
        Az LLM kimenetének formátuma:
        {
            "type": "játék" | "weblap" | ...,
            "components": ["karakter", "ellenség"],
            "title": "...",
            "description": "...",
            "params": {...}
        }
        """
        self._last_plan = llm_json
        
        goal_type = llm_json.get("type", "")
        components = llm_json.get("components", [])
        title = llm_json.get("title", "")
        params = llm_json.get("params", {})
        
        # === JÁTÉK ===
        if goal_type == "játék":
            # Összeállítjuk a feladat szöveget
            goal_parts = ["keszits egy jatekot"]
            for comp in components:
                # Magyar toldalékok táblázatból
                suffix_map = {"karakter": "rel", "ellenseg": "gel", "ellenség": "gel",
                             "lövedék": "kel", "platform": "mal", "pont": "tal",
                             "menü": "vel", "játékos": "sal", "szint": "en"}
                suffix = suffix_map.get(comp, "val")
                goal_parts.append(comp + suffix)
            goal = " ".join(goal_parts)
            
            # Terv
            plan = self.planner.plan(goal)
            if not plan or not plan.steps:
                # Ha a terv nem sikerült, próbáljuk egyszerűbben
                goal = "keszits egy akcio jatekot"
                plan = self.planner.plan(goal)
                if not plan:
                    return None
            
            # LLM paraméterek beállítása a Generator számára
            # A generator a _game_params-t használja
            color_schemes = [
                ("(0, 102, 204)", "(255, 50, 50)", "(240, 248, 255)"),
                ("(50, 205, 50)", "(255, 165, 0)", "(30, 30, 40)"),
                ("(147, 0, 211)", "(255, 215, 0)", "(245, 245, 220)"),
                ("(255, 20, 147)", "(0, 255, 255)", "(25, 25, 35)"),
                ("(0, 255, 127)", "(255, 0, 255)", "(240, 240, 240)"),
            ]
            cs = params.get("color_scheme", 0)
            if isinstance(cs, int) and 0 <= cs < len(color_schemes):
                scheme = color_schemes[cs]
            else:
                scheme = color_schemes[0]
            
            self.generator._game_params = {
                "{player_color}": scheme[0],
                "{enemy_color}": scheme[1],
                "{bg_color}": scheme[2],
                "{player_speed}": str(params.get("player_speed", 5)),
                "{player_size}": str(params.get("player_size", 50)),
                "{enemy_size}": str(params.get("enemy_size", 40)),
                "{enemy_speed_min}": str(params.get("enemy_speed_min", 2)),
                "{enemy_speed_max}": str(params.get("enemy_speed_max", 5)),
                "{spawn_rate}": str(params.get("spawn_rate", 0.02)),
                "{game_title}": title or "DKA V3 Játék",
                "{game_over_text}": "GAME OVER",
            }
            
            code = self.generator.generate(plan, "python")
            return code
        
        # === WEBLAP ===
        elif goal_type == "weblap":
            goal = "keszits egy weblapot"
            if components:
                comp_str = " ".join(components[:3])
                goal = f"keszits egy weblapot {comp_str}val"
            
            plan = self.planner.plan(goal)
            if not plan:
                return None
            
            # Téma beállítása
            theme = params.get("theme", "általános")
            ctx = self.generator._get_topic_context(goal)
            if title:
                ctx["header_title"] = title
            
            code = self.generator.generate(plan, "html")
            return code
        
        # === ALGORITMUS ===
        elif goal_type == "algoritmus":
            alg_name = components[0] if components else "buborékrendezés"
            goal = f"csinálj egy {alg_name} algoritmust"
            
            plan = self.planner.plan(goal)
            if not plan:
                return None
            
            code = self.generator.generate(plan, "python")
            return code
        
        return None
    
    def generate_from_text(self, goal: str) -> Optional[dict[str, str] | str]:
        """Közvetlen szövegből generál (LLM nélkül, standard DKA)."""
        plan = self.planner.plan(goal)
        if not plan:
            return None
        
        lang = "python" if any(w in goal for w in ["függvény", "osztály", "algoritmus",
                                                     "játék", "jatek", "rendez", "szur",
                                                     "számol", "lista", "faktoriális",
                                                     "fibonacci", "buborék", "prím",
                                                     "palindrom", "gráf"]) else "html"
        return self.generator.generate(plan, lang)
    
    def get_last_plan(self) -> Optional[dict]:
        """Visszaadja az utolsó LLM tervet (debug)."""
        return self._last_plan
