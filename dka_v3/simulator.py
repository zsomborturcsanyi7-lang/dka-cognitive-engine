"""
DKA V3 — Simulator
===================
A szimulátor. Lefuttatja a tervet a "fejében", mielőtt
a Generator kódot gyártana belőle.

Cél: ellenőrizni, hogy a terv elvezet-e a kívánt eredményhez.
Nem futtatja a kódot! A fogalmi szinten szimulál:
  - "van egy listám" → gyűjtemény
  - "szűröm párosra" → gyűjtemény (szűrt)
  - "kell egy HTML űrlap" → weblap része

Minden lépés után:
  1. Frissíti a "világ állapotát" (milyen fogalmak élnek)
  2. Ellenőrzi, hogy a következő lépés inputja rendelkezésre áll-e
  3. Ha nem, jelzi a hiányzó fogalmat

Ezzel a DKA "látja" a gondolatmenetét, mielőtt kódot írna.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from concept_graph import ConceptGraph, Concept, RelationType
from planner import Plan, PlanStep


@dataclass
class SimState:
    """A szimuláció belső állapota. Mit "tud" a DKA egy adott pillanatban."""
    variables: dict[str, str] = field(default_factory=dict)
    # variable_name → concept_name
    
    active_concepts: set[str] = field(default_factory=set)
    # Mik azok a fogalmak, amik jelenleg "élnek" a rendszerben
    
    constraints: list[str] = field(default_factory=list)
    # Aktív feltételek (pl. "x páros")
    
    output: list[str] = field(default_factory=list)
    # A szimuláció eddigi kimenete
    
    issues: list[str] = field(default_factory=list)
    # Problémák amiket talált
    
    def clone(self) -> SimState:
        """Állapot másolása (elágazásokhoz)."""
        return SimState(
            variables=dict(self.variables),
            active_concepts=set(self.active_concepts),
            constraints=list(self.constraints),
            output=list(self.output),
            issues=list(self.issues),
        )


class Simulator:
    """
    Fogalmi szimulátor.
    
    Nem futtat kódot! A fogalmak szintjén szimulál:
    - "van egy listám" → active_concepts: {gyűjtemény}
    - "szűröm" → active_concepts: {gyűjtemény, szűrés, feltétel}
    - "HTML formot akarok" → active_concepts: {űrlap, input_mező, weblap}
    
    Minden lépés után frissíti az állapotot, és jelzi ha
    valami hiányzik.
    """
    
    def __init__(self, graph: ConceptGraph):
        self.graph = graph
    
    def simulate(self, plan: Plan) -> SimState:
        """
        Terv végigszimulálása.
        Visszaadja a végső állapotot (hibákkal együtt).
        """
        state = SimState()
        
        # Kezdőállapot: input fogalmak
        for concept in plan.input_concepts:
            state.active_concepts.add(concept)
            c = self.graph.get(concept)
            if c:
                # IS_A lánc követése
                for rel in c.relations:
                    if rel.type == RelationType.IS_A:
                        state.active_concepts.add(rel.target_name)
        
        for step in plan.steps:
            state = self._simulate_step(step, state)
        
        # Végső ellenőrzés: elértük a kívánt kimenetet?
        if plan.output_concept and plan.output_concept not in state.active_concepts:
            state.issues.append(
                f"A kívánt kimenet '{plan.output_concept}' nem jött létre. "
                f"Aktív fogalmak: {', '.join(sorted(state.active_concepts))}"
            )
        
        return state
    
    def _simulate_step(self, step: PlanStep, state: SimState) -> SimState:
        """Egy tervlépés szimulálása."""
        new_state = state.clone()
        
        action_concept = self.graph.get(step.action)
        if not action_concept:
            new_state.issues.append(f"Ismeretlen művelet: '{step.action}'")
            return new_state
        
        # 1. Input ellenőrzés: minden REQUIRES teljesül?
        for rel in action_concept.relations:
            if rel.type == RelationType.REQUIRES:
                required = rel.target_name
                if required not in new_state.active_concepts:
                    # Lehet, hogy a step target-je biztosítja?
                    if step.target != required:
                        # Lehet, hogy egy IS_A kapcsolaton keresztül?
                        found = False
                        for active in new_state.active_concepts:
                            path = self.graph.shortest_path(active, required)
                            if path:
                                found = True
                                break
                        if not found:
                            new_state.issues.append(
                                f"A '{step.action}' művelethez hiányzik '{required}'. "
                                f"Rendelkezésre: {', '.join(sorted(new_state.active_concepts))}"
                            )
        
        # 2. Gyerek lépések szimulálása (pl. feltételek)
        for child in step.children:
            new_state = self._simulate_step(child, new_state)
        
        # 3. Output frissítés: minden PRODUCES hozzáadása az aktív fogalmakhoz
        for rel in action_concept.relations:
            if rel.type == RelationType.PRODUCES:
                new_state.active_concepts.add(rel.target_name)
                
                # Ha a PRODUCES valaminek IS_A-ja, azt is adjuk hozzá
                produced = self.graph.get(rel.target_name)
                if produced:
                    for prod_rel in produced.relations:
                        if prod_rel.type == RelationType.IS_A:
                            new_state.active_concepts.add(prod_rel.target_name)
        
        # 4. Változó kezelés: ha van target, azt is felvehetjük
        if step.target and step.target not in new_state.active_concepts:
            new_state.active_concepts.add(step.target)
        
        # 5. Constraint-ek kezelése (gyerek lépésekből)
        for child in step.children:
            if child.action == "feltétel" and child.description:
                new_state.constraints.append(child.description)
        
        return new_state
    
    def compare(self, state_a: SimState, state_b: SimState) -> dict:
        """
        Két állapot összehasonlítása.
        Hasznos: "ez a terv jobb, mint az a terv?"
        """
        return {
            "concepts_gained": state_b.active_concepts - state_a.active_concepts,
            "concepts_lost": state_a.active_concepts - state_b.active_concepts,
            "issues_a": len(state_a.issues),
            "issues_b": len(state_b.issues),
            "a_better": len(state_a.issues) < len(state_b.issues),
            "b_better": len(state_b.issues) < len(state_a.issues),
        }
    
    def report(self, state: SimState) -> str:
        """Szimulációs jelentés embereknek."""
        lines = []
        lines.append("=== SZIMULÁCIÓS JELENTÉS ===")
        lines.append(f"Aktív fogalmak: {', '.join(sorted(state.active_concepts))}")
        if state.constraints:
            lines.append(f"Feltételek: {', '.join(state.constraints)}")
        if state.variables:
            lines.append("Változók:")
            for name, concept in state.variables.items():
                lines.append(f"  {name}: {concept}")
        if state.issues:
            lines.append(f"\nProblémák ({len(state.issues)}):")
            for issue in state.issues:
                lines.append(f"  ! {issue}")
        else:
            lines.append("\nNincs probléma — a terv végrehajtható.")
        return "\n".join(lines)
