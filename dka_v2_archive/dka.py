"""
DKA Core — Main Entry Point
============================
A teljes rendszer összekötése.

Hasznalat:
    from dka_core import DKA
    dka = DKA()
    dka.learn('def hello(): print("world")')
    result = dka.reason("create a greeting function")
    print(result)
"""

from __future__ import annotations
import os
from typing import Optional
from collections import defaultdict

from node_types import NodeType, DataDomain
from hypergraph_v2 import HypergraphV2
from grammar_parser import GrammarParser
from constructive_generator import ConstructiveGenerator
from inference_engine_v2 import InferenceEngineV2
from schema_engine import SchemaEngine
from semantic_layer import SemanticIndex, SemanticExtractor
from synthesis_engine_v2 import SynthesisEngineV2


class DKA:
    """
    Determinisztikus Kognitiv Architektura V2
    
    A haromretegu hipergraf + GrammarParser + ConstructiveGenerator
    + InferenceEngine egyesitese.
    """
    
    def __init__(self):
        self.graph = HypergraphV2()
        self.parser = GrammarParser()
        self.generator = ConstructiveGenerator(self.graph)
        self.inference = InferenceEngineV2(self.graph)
        self.schemas = SchemaEngine(self.graph)
        self.semantics = SemanticIndex(self.graph)
        self.synthesis = SynthesisEngineV2(self.graph, self.semantics, self.generator)
        self._learned_sources = set()
    
    def learn(self, code: str, domain: DataDomain = DataDomain.GENERAL,
              source: str = "") -> int:
        """Python kod tanulasa."""
        old_count = self.graph.total_pies
        nodes = self.parser.parse(code, domain=domain, source=source)
        nids = self.graph.ingest_pattern_tree(nodes, domain=domain, source=source)
        
        if source:
            self._learned_sources.add(source)
        
        new_pies = self.graph.total_pies - old_count
        
        # Szemantikus index frissítése
        self.semantics.index_new()
        
        # Értelmes séma építés a SchemaEngine-n keresztül
        patterns = self.graph.discover_patterns(min_instances=2)
        if patterns:
            for p in patterns[:5]:
                # Típus alapján értelmes név
                sig = p['signature'].split('|')[0].lower()
                type_name = p['signature'].split('|')[0].lower() if '|' in p['signature'] else p['signature'][:20]
                
                # Próbáljunk értelmes nevet adni
                schema_name = self._generate_schema_name(p)
                
                if len(p['pattern_ids']) >= 2:
                    existing = [s for s in self.graph.schemas.values() if s.name == schema_name]
                    if not existing:
                        self.schemas.create_schema(
                            name=schema_name,
                            pattern_ids=p['pattern_ids'],
                            domain=domain
                        )
        
        return new_pies
    
    def _generate_schema_name(self, pattern_info: dict) -> str:
        """Értelmes séma név generálása a minta alapján."""
        sig = pattern_info['signature']
        nid = pattern_info['pattern_ids'][0]
        pattern = self.graph.patterns.get(nid)
        if not pattern:
            return f"auto_{sig.split('|')[0].lower()[:20]}"
        
        # Típus alapján
        type_name = pattern.type.name.lower()
        
        # Próbáljunk kontextust találni
        parent_info = ""
        for pid2, p2 in self.graph.patterns.items():
            for role, children in p2.children.items():
                for child in children:
                    if child.id == nid:
                        parent_info = f"in_{p2.type.name.lower()}"
                        break
        
        count = pattern_info['count']
        type_counts = {
            NodeType.IF_STATEMENT: "conditional",
            NodeType.FOR_LOOP: "iteration",
            NodeType.WHILE_LOOP: "iteration",
            NodeType.ASSIGNMENT: "assignment",
            NodeType.FUNCTION_CALL: "call",
            NodeType.RETURN_STMT: "return",
            NodeType.COMPARISON: "comparison",
            NodeType.FUNCTION_DEF: "function",
        }
        label = type_counts.get(pattern.type, type_name)
        
        if parent_info:
            return f"{label}_{parent_info}"
        return f"{label}_x{count}"
    
    def learn_file(self, path: str, domain: DataDomain = DataDomain.GENERAL) -> int:
        """Fajl betoltese es tanulasa."""
        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()
        return self.learn(code, domain=domain, source=path)
    
    def generate(self, nid: str = None, goal: str = None) -> str:
        """Kod generalasa nodus IDbol, celbol, vagy szemantikus keresessel."""
        if nid:
            return self.generator.generate_from_ids(nid)
        
        if goal:
            # 1. ELSO: szemantikus keresés — pontos név egyezés magas prioritás
            sem_results = self.semantics.search_by_text(goal, top_k=5)
            func_results = [r for r in sem_results 
                          if r['type'] == 'FUNCTION_DEF']
            
            high_confidence = False
            if func_results:
                best = func_results[0]
                # SZIGORÚ feltétel:
                # 1. Összes név szó a goal-ban van (pontos névillesztés), VAGY
                # 2. Relevancia ≥ 0.6 ÉS legalább 2 név szó egyezik, VAGY
                # 3. Relevancia ≥ 0.7 ÉS legalább 1 név szó egyezik
                name_words = set(best['name'].lower().replace('_', ' ').split() 
                               if best['name'] else [])
                goal_words = set(goal.lower().split())
                all_names_in_goal = bool(name_words) and name_words <= goal_words
                has_word_overlap = bool(name_words & goal_words)
                overlap_count = len(name_words & goal_words)
                
                is_confident = (all_names_in_goal or
                               (best['relevance'] >= 0.6 and overlap_count >= 2) or
                               (best['relevance'] >= 0.7 and overlap_count >= 1))
                
                if is_confident:
                    high_confidence = True
                    for r in func_results[:2]:
                        self.semantics.learn_from_feedback(goal, r['id'], True)
                    best_id = func_results[0]['id']
                    return self.generator.generate_from_ids(best_id)
            
            # 2. SCAFFOLD rendszer — új program alkotása ismert mintákból
            # (a scaffold KULCSSZAVAS egyezés, magas prioritás — a mutáció ELŐTT)
            scaffold_code = None
            try:
                from struct_compose_v3 import StructuredComposerV3, ProgramScaffoldV3
                if ProgramScaffoldV3.select(goal) is not None:
                    composer = StructuredComposerV3(self.graph, self.semantics)
                    scaffold_code = composer.compose(goal)
                    if scaffold_code and scaffold_code.strip():
                        return scaffold_code
            except Exception:
                pass
            
            # 3. Mutáció próbálása (ha nincs jó szemantikus találat és nincs scaffold)
            if not high_confidence and not scaffold_code:
                try:
                    from pattern_mutator import PatternMutator, GoalAnalyzer
                    ga = GoalAnalyzer()
                    analysis = ga.analyze(goal)
                    if analysis["action"]:
                        mutator = PatternMutator(self.graph, self.generator, self.semantics)
                        result = mutator.mutate_for_goal(goal)
                        if result and result.strip():
                            return result
                except Exception:
                    pass
            
            # 4. SCAFFOLD rendszer — új program alkotása ismert mintákból
            # (a scaffold garantáltan valid Python, ha van egyezés)
            try:
                from struct_compose_v3 import StructuredComposerV3
                composer = StructuredComposerV3(self.graph, self.semantics)
                result = composer.compose(goal)
                if result and result.strip():
                    return result
            except Exception:
                pass
            
            # 5. Próbáljuk a SynthesisEngine V2-t
            result = self.synthesis.synthesize(goal)
            if result and result.strip():
                return result
            
            # 6. Utolsó: típus alapú keresés (csak ha semmi más nem működött)
            available_types = [
                NodeType.FUNCTION_DEF, NodeType.FOR_LOOP,
                NodeType.IF_STATEMENT, NodeType.RETURN_STMT,
                NodeType.ASSIGNMENT, NodeType.FUNCTION_CALL,
                NodeType.WHILE_LOOP, NodeType.CLASS_DEF,
            ]
            result = self.inference.synthesize(goal, available_types)
            if result:
                return self.generator.generate(result[0])
        
        return ""
    
    def reason(self, prompt: str) -> str:
        """Magas szintu kovetkeztetes."""
        output = []
        output.append(f"DKA V2 Input: '{prompt}'")
        # Szemantikus keresés
        sem_results = self.semantics.search_by_text(prompt, top_k=3)
        if sem_results:
            output.append(f"[Szemantikus] {len(sem_results)} talalat:")
            for r in sem_results:
                output.append(f"  - {r['type']}: {r['name']} (rel: {r['relevance']})")
                
                code = self.generator.generate_from_ids(r['id'])
                if code:
                    first_line = code.split(chr(10))[0][:80]
                    output.append(f"    {first_line}")
                
                self.semantics.learn_from_feedback(prompt, r['id'], True)
        
        output.append("")
        
        stats = self.graph.stats()
        output.append(f"[Tudasbazis] {stats['total_pie']} PIE, "
                      f"{stats['primitives']} primitiv, "
                      f"{stats['patterns']} minta, "
                      f"{stats['schemas']} sema")
        
        generated = self.generate(goal=prompt)
        if generated:
            output.append("")
            output.append("[Generalrt Kod]")
            output.append(generated)
            
            try:
                compile(generated, '<dka_output>', 'exec')
                output.append("")
                output.append("[OK] A kod valid Python.")
            except SyntaxError as e:
                output.append("")
                output.append(f"[Figyelmeztetes] Szintaxis hiba: {e}")
        else:
            output.append("")
            output.append("[Nincs talalat] Nincs eleg tudas a grafban.")
        
        # Séma validáció
        schema_stats = self.schemas.stats()
        if schema_stats["schemas"] > 0:
            output.append("")
            output.append(f"[Semak] {schema_stats['schemas']} sema, "
                        f"{schema_stats['total_constraints']} megszoritas")
            
            # Mutassuk a sémákat
            for schema in list(self.graph.schemas.values())[:5]:
                output.append(f"  - {schema.name}: {len(schema.pattern_ids)} minta")
        
        top_nodes = self.graph.find_by_type(NodeType.FUNCTION_DEF)
        if top_nodes:
            output.append("")
            output.append("[Analógia] Legkozelebbi tanult minta:")
            for node in top_nodes[:2]:
                name_node = node.children.get("name", [None])[0] if node.children.get("name") else None
                name = name_node.value if name_node else "?"
                output.append(f"  - {node.type.name}: {name}")
        
        return "\n".join(output)
    
    def inspect(self) -> str:
        """Graf belso allapotanak kiirasa."""
        stats = self.graph.stats()
        
        lines = []
        lines.append("DKA Belso Allapot")
        lines.append("=" * 50)
        lines.append(f"Osszes PIE: {stats['total_pie']}")
        lines.append(f"  1. reteg (Primitiv): {stats['primitives']}")
        lines.append(f"  2. reteg (Minta):    {stats['patterns']}")
        lines.append(f"  3. reteg (Sema):     {stats['schemas']}")
        lines.append("")
        
        type_counts = {}
        for pattern in self.graph.patterns.values():
            tname = pattern.type.name
            type_counts[tname] = type_counts.get(tname, 0) + 1
        
        if type_counts:
            lines.append("Minta tipusok:")
            for tname, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  {tname}: {count}")
        
        if self.graph.schemas:
            lines.append("")
            lines.append("Semak:")
            for schema in self.graph.schemas.values():
                lines.append(f"  {schema.name}: {len(schema.pattern_ids)} minta, "
                           f"{len(schema.associations)} asszociacio")
        
        # SchemaEngine megszorítások
        schema_stats = self.schemas.stats()
        lines.append("")
        lines.append("SchemaEngine:")
        lines.append(f"  Osszes megszoritas: {schema_stats['total_constraints']}")
        lines.append(f"  Atlag/sema: {schema_stats['avg_constraints_per_schema']:.1f}")
        
        # Szemantikus index
        sem_stats = self.semantics.stats()
        lines.append("")
        lines.append("Szemantikus Index:")
        lines.append(f"  Fogalmak: {sem_stats['total_concepts']}")
        lines.append(f"  Indexelt mintak: {sem_stats['total_indexed_patterns']}")
        lines.append(f"  Interakciok: {sem_stats['total_searches']}")
        
        return "\n".join(lines)
    
    def save(self, path: str):
        self.graph.to_json_file(path)
        # SchemaEngine constraints mentés
        import json
        constraint_data = {}
        for sid, constraints in self.schemas.constraints.items():
            constraint_data[sid] = [
                {"role_path": c.role_path, "constraints": c.constraints, "importance": c.importance}
                for c in constraints
            ]
        cpath = path.replace('.json', '_schemas.json')
        with open(cpath, 'w', encoding='utf-8') as f:
            json.dump(constraint_data, f, indent=2)
        
        # Szemantikus index mentése
        spath = path.replace('.json', '_semantics.json')
        sem_data = {
            "concept_index": {c: list(ids) for c, ids in self.semantics.concept_index.items()},
            "pattern_semantics": {pid: list(concepts) for pid, concepts in self.semantics.pattern_semantics.items()},
            "concept_usage": dict(self.semantics.concept_usage),
            "search_history": {q: dict(c) for q, c in self.semantics.search_history.items()},
        }
        with open(spath, 'w', encoding='utf-8') as f:
            json.dump(sem_data, f, indent=2)
    
    def load(self, path: str):
        self.graph = HypergraphV2.from_json_file(path)
        self.generator = ConstructiveGenerator(self.graph)
        self.inference = InferenceEngineV2(self.graph)
        self.schemas = SchemaEngine(self.graph)
        self.semantics = SemanticIndex(self.graph)
        
        # SchemaEngine constraints visszatöltése
        import json
        from schema_engine import SchemaConstraint
        cpath = path.replace('.json', '_schemas.json')
        if os.path.exists(cpath):
            with open(cpath, 'r', encoding='utf-8') as f:
                constraint_data = json.load(f)
            for sid, constraints_list in constraint_data.items():
                self.schemas.constraints[sid] = [
                    SchemaConstraint(c["role_path"], c["constraints"], c["importance"])
                    for c in constraints_list
                ]
        
        # Szemantikus index visszatöltése
        spath = path.replace('.json', '_semantics.json')
        if os.path.exists(spath):
            with open(spath, 'r', encoding='utf-8') as f:
                sem_data = json.load(f)
            self.semantics.concept_index = defaultdict(set,
                {c: set(ids) for c, ids in sem_data.get("concept_index", {}).items()}
            )
            self.semantics.pattern_semantics = defaultdict(set,
                {pid: set(concepts) for pid, concepts in sem_data.get("pattern_semantics", {}).items()}
            )
            self.semantics.concept_usage.update(sem_data.get("concept_usage", {}))
            for q, c in sem_data.get("search_history", {}).items():
                self.semantics.search_history[q].update(c)
        
        # Már indexeltnek jelöljük a visszatöltött mintákat
        self.semantics.index_new()
    
    def stats(self) -> dict:
        return self.graph.stats()


if __name__ == "__main__":
    import sys
    
    dka = DKA()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "learn" and len(sys.argv) > 2:
            path = sys.argv[2]
            if os.path.exists(path):
                count = dka.learn_file(path)
                print(f"Betanulva: {count} uj PIE")
                print(dka.inspect())
            else:
                print(f"Nem talalhato: {path}")
        
        elif cmd == "reason":
            prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "create a function"
            print(dka.reason(prompt))
        
        elif cmd == "inspect":
            print(dka.inspect())
        
        elif cmd == "save" and len(sys.argv) > 2:
            dka.save(sys.argv[2])
            print(f"Elmentve: {sys.argv[2]}")
        
        elif cmd == "load" and len(sys.argv) > 2:
            dka.load(sys.argv[2])
            print(f"Betoltve: {sys.argv[2]}")
            print(dka.inspect())
        
        else:
            print("Hasznalat:")
            print("  python -m dka_core.main learn <file.py>")
            print("  python -m dka_core.main reason <prompt>")
            print("  python -m dka_core.main inspect")
            print("  python -m dka_core.main save <file.json>")
            print("  python -m dka_core.main load <file.json>")
    else:
        print("DKA V2 Interaktiv mod")
        print("=" * 50)
        
        samples = [
            ("bubble_sort", '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''),
            ("fibonacci", '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
'''),
            ("api_handler", '''
def fetch_user(user_id):
    url = f"https://api.example.com/users/{user_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None
'''),
        ]
        
        for name, code in samples:
            count = dka.learn(code, source=name)
            print(f"  Tanultam: {name} ({count} PIE)")
        
        print()
        print(dka.inspect())
        print()
        print(dka.reason("sort numbers"))
