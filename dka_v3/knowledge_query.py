"""
DKA V3 — KnowledgeQuery
========================
A DKA saját tudásának lekérdezése.

Lehetővé teszi, hogy a DKA-t megkérdezzük:
  "Mit tudsz a játékokról?"
  "Milyen szabályokat tanultál eddig?"
  "Mi az a 'kártya'?"
  "Hány fogalmat ismersz?"

Válasz: a saját ConceptGraph-jából, a tanult szabályokból
és a felfedezések naplójából építi fel a választ.
"""

from concept_graph import ConceptGraph, RelationType
from planner import GoalParser


class KnowledgeQuery:
    """
    Tudás lekérdező.
    A DKA saját belső tudását kérdezi le természetes nyelven.
    """
    
    def __init__(self, graph: ConceptGraph, parser: GoalParser):
        self.graph = graph
        self.parser = parser
    
    def ask(self, question: str) -> str:
        """Kérdés megválaszolása a DKA tudása alapján."""
        q = question.lower()
        lines = []
        
        # === 1. STATISZTIKA KÉRDÉSEK ===
        if "hány" in q or "hany" in q or "mennyi" in q:
            s = self.graph.stats()
            lines.append("📊 **Statisztika:**")
            lines.append(f"  Fogalmak: {s['concepts']}")
            lines.append(f"  Kapcsolatok: {s['relations']}")
            lines.append(f"  Műveletek: {s['operations']}")
            lines.append(f"  Szó→akció szabályok: {len(self.parser._task_patterns)}")
        
        if "hány" in q and "szabály" in q:
            lines.append(f"  Összes szó→akció szabály: {len(self.parser._task_patterns)}")
        
        # === 2. FOGALOM LEKÉRDEZÉS ===
        # "Mit tudsz a ...ról/ről", "Mi az a ...", "Ismered a ..."
        for concept_name in self.graph.concepts:
            if concept_name.lower() in q and len(concept_name) > 2:
                concept = self.graph.get(concept_name)
                if concept:
                    lines.append(f"\n**{concept_name}:**")
                    if concept.description:
                        lines.append(f"  Leírás: {concept.description}")
                    
                    if concept.relations:
                        lines.append("  Kapcsolatok:")
                        for rel in concept.relations[:5]:
                            lines.append(f"    {rel.type.name} → {rel.target_name} (erősség: {rel.strength:.1f})")
                    
                    if concept.properties:
                        lines.append("  Tulajdonságok:")
                        for prop in concept.properties:
                            lines.append(f"    {prop.name}: {prop.description}")
                    
                    if concept.operations:
                        lines.append("  Műveletek:")
                        for op in concept.operations:
                            lines.append(f"    {op.name}: {op.description}")
                    
                    if concept.language_mappings:
                        lines.append("  Nyelvi leképzések:")
                        for lang, mapping in concept.language_mappings.items():
                            lines.append(f"    {lang}: {mapping}")
        
        # === 3. SZINONÍMA KERESÉS ===
        # "Mi a különbség X és Y között?"
        # "X más néven?"
        for concept in self.graph.concepts.values():
            for rel in concept.relations:
                if rel.type == RelationType.SAME_AS and rel.target_name.lower() in q:
                    lines.append(f"\n  '{concept.name}' szinonimája: '{rel.target_name}'")
        
        # === 4. KAPCSOLAT KERESÉS ===
        # "Mi kapcsolódik a ...hoz/hez"
        target_word = None
        for w in q.split():
            for cn in self.graph.concepts:
                if w == cn.lower() or w.startswith(cn.lower()):
                    target_word = cn
                    break
            if target_word:
                break
        
        if target_word and "kapcsol" in q:
            lines.append(f"\n**{target_word} kapcsolatai:**")
            concept = self.graph.get(target_word)
            if concept:
                for rel in concept.relations:
                    lines.append(f"  {rel.type.name} → {rel.target_name}")
                # Fordított kapcsolatok
                lines.append("  Fordított kapcsolatok:")
                for other in self.graph.concepts.values():
                    for rel in other.relations:
                        if rel.target_name == target_word:
                            lines.append(f"    {other.name} {rel.type.name} → {target_word}")
        
        # === 5. TANULT SZABÁLYOK ===
        if "tanult" in q or "szabály" in q or "tudsz" in q:
            # Csoportosítsuk a szabályokat akció szerint
            action_groups = {}
            for word, (action, target) in self.parser._task_patterns.items():
                if action not in action_groups:
                    action_groups[action] = []
                action_groups[action].append(word)
            
            action_groups = {a: w for a, w in action_groups.items() if a is not None}
            lines.append(f"\n**Tanult szó→akció szabályok ({len(self.parser._task_patterns)} db):**")
            for action, words in sorted(action_groups.items()):
                lines.append(f"  {action}: {', '.join(words[:8])}")
        
        # === 6. HIERARCHIA ===
        if "része" in q or "tartalmaz" in q or "hierarchia" in q:
            parts = {}
            for concept in self.graph.concepts.values():
                for rel in concept.relations:
                    if rel.type == RelationType.PART_OF:
                        if rel.target_name not in parts:
                            parts[rel.target_name] = []
                        parts[rel.target_name].append(concept.name)
            
            lines.append("\n**Hierarchia (részei):**")
            for parent, children in sorted(parts.items()):
                lines.append(f"  {parent}:")
                for child in children[:8]:
                    lines.append(f"    - {child}")
        
        # === 7. HA NINCS VÁLASZ ===
        if not lines:
            lines.append("🤔 **Nem találok erre a kérdésre választ a tudásomban.**")
            lines.append("Próbáld másképp:")
            lines.append("  • \"Mit tudsz a [fogalom]-ról?\"")
            lines.append("  • \"Hány fogalmat ismersz?\"")
            lines.append("  • \"Mi kapcsolódik a [fogalom]-hoz?\"")
            lines.append("  • \"Milyen szabályokat tanultál?\"")
        
        return "\n".join(lines)
