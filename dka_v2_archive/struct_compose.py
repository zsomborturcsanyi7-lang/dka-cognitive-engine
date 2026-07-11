"""
DKA Core — Structure Composition Engine
========================================
A ReasoningEngine hiányzó része: hogyan rakjunk össze több mintát
egy koherens programmá, struktúra szinten (nem szövegként).

Folyamat:
1. Scaffold: üres programváz létrehozása (FUNCTION_DEF + BLOCK + ...)
2. Slotok: a váz meghatározza, hova mit kell rakni
3. Filling: minden slotba a legjobb minta, klónozva + adaptálva
4. Validálás: változók definiálva? struktúra helyes?
5. Generálás
"""

from __future__ import annotations
from typing import Optional, Callable
from dataclasses import dataclass, field
from node_types import (
    BaseNode, PrimitiveNode, PatternNode,
    NodeType, DataDomain, Role,
)
from hypergraph_v2 import HypergraphV2
from constructive_generator import ConstructiveGenerator
from semantic_layer import SemanticIndex
from pattern_intel import PatternIntelligence
from inference_engine_v2 import InferenceEngineV2


# ═══════════════════════════════════════════════════════════════════
# 1. SCAFFOLD: programvázak
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ScaffoldSlot:
    """Egy hely a programvázban, ahova mintát kell tenni."""
    role: str                   # "body_stmt", "loop_body", "if_condition"
    target_type: NodeType       # Milyen típusú minta kell ide
    description: str            # Mit kell csinálnia
    parent_path: list[str]      # Hol van a scaffoldban
    required: bool = True
    filled: bool = False


class ProgramScaffold:
    """
    Programváz: egy üres funkció struktúra, amit később kitöltünk.
    
    Pl. egy számkitalálós játék váz:
    ```
    def guess_game():
        target = ___  # random szám
        while True:
            guess = ___  # input
            if ___ :     # összehasonlítás
                ___      # talált
            else:
                ___      # nem talált
    ```
    
    A ___ helyek a "slotok", amiket a PatternComposer tölt ki.
    """
    
    # Ismert feladat → váz sablonok
    TEMPLATES = {}
    
    @staticmethod
    def guess_game(name: str = "guess_game") -> PatternNode:
        """Számkitalálós játék váz."""
        # target = random.randint(1, 100)
        init_target = PatternNode(type=NodeType.ASSIGNMENT,
            roles={"targets": Role("targets"), "value": Role("value")})
        init_target.children["targets"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value="target")]
        init_target.children["value"] = [
            PatternNode(type=NodeType.FUNCTION_CALL)]  # kitöltendő
        
        # while True:
        loop = PatternNode(type=NodeType.WHILE_LOOP,
            roles={"condition": Role("condition"), "body": Role("body")})
        loop.children["condition"] = [
            PrimitiveNode(type=NodeType.LITERAL, value="True")]
        
        loop_body = PatternNode(type=NodeType.BLOCK,
            roles={"statements": Role("statements")})
        loop.children["body"] = [loop_body]
        
        # guess = input()
        get_guess = PatternNode(type=NodeType.ASSIGNMENT,
            roles={"targets": Role("targets"), "value": Role("value")})
        get_guess.children["targets"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value="guess")]
        get_guess.children["value"] = [
            PatternNode(type=NodeType.FUNCTION_CALL)]  # PattenNode placeholder
        
        # if guess == target:
        if_stmt = PatternNode(type=NodeType.IF_STATEMENT,
            roles={"condition": Role("condition"), "body": Role("body"),
                   "orelse": Role("orelse")})
        if_stmt.children["condition"] = [
            PatternNode(type=NodeType.COMPARISON)]
        if_stmt.children["body"] = [
            PatternNode(type=NodeType.BLOCK,
                roles={"statements": Role("statements")})]
        if_stmt.children["orelse"] = [
            PatternNode(type=NodeType.BLOCK,
                roles={"statements": Role("statements")})]
        
        loop_body.children["statements"] = [get_guess, if_stmt]
        
        # FUNCTION_DEF
        func = PatternNode(type=NodeType.FUNCTION_DEF,
            roles={"name": Role("name"), "body": Role("body")})
        func.children["name"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=name)]
        
        main_body = PatternNode(type=NodeType.BLOCK,
            roles={"statements": Role("statements")})
        main_body.children["statements"] = [init_target, loop]
        func.children["body"] = [main_body]
        
        return func
    
    @staticmethod
    def data_processor(name: str = "process_data") -> PatternNode:
        """Adatfeldolgozó váz: open → transform → return."""
        assign_data = PatternNode(type=NodeType.ASSIGNMENT,
            roles={"targets": Role("targets"), "value": Role("value")})
        assign_data.children["targets"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value="data")]
        
        ret = PatternNode(type=NodeType.RETURN_STMT,
            roles={"value": Role("value")})
        ret.children["value"] = [PrimitiveNode(type=NodeType.VARIABLE, value="data")]
        
        body = PatternNode(type=NodeType.BLOCK,
            roles={"statements": Role("statements")})
        body.children["statements"] = [assign_data, ret]
        
        func = PatternNode(type=NodeType.FUNCTION_DEF,
            roles={"name": Role("name"), "params": Role("params"),
                   "body": Role("body")})
        func.children["name"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=name)]
        func.children["params"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value="path",
                         role="param")]
        func.children["body"] = [body]
        
        return func
    
    @staticmethod
    def simple_function(name: str = "process") -> PatternNode:
        """Egyszerű függvény váz: def name(params): body."""
        body = PatternNode(type=NodeType.BLOCK,
            roles={"statements": Role("statements")})
        body.children["statements"] = []
        
        func = PatternNode(type=NodeType.FUNCTION_DEF,
            roles={"name": Role("name"), "body": Role("body")})
        func.children["name"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=name)]
        func.children["body"] = [body]
        
        return func

    @staticmethod
    def word_counter(name="word_frequency"):
        from node_types import PatternNode as PN, PrimitiveNode as PR, NodeType, Role
        ra = PN(type=NodeType.ASSIGNMENT, roles={"targets": Role("targets"), "value": Role("value")})
        ra.children["targets"] = [PR(type=NodeType.VARIABLE, value="text")]
        ra.children["value"] = [PN(type=NodeType.FUNCTION_CALL)]
        sa = PN(type=NodeType.ASSIGNMENT, roles={"targets": Role("targets"), "value": Role("value")})
        sa.children["targets"] = [PR(type=NodeType.VARIABLE, value="words")]
        sa.children["value"] = [PN(type=NodeType.FUNCTION_CALL)]
        cl = PN(type=NodeType.FOR_LOOP, roles={"target": Role("target"), "iter": Role("iter"), "body": Role("body")})
        cl.children["target"] = [PR(type=NodeType.VARIABLE, value="word")]
        cl.children["iter"] = [PR(type=NodeType.VARIABLE, value="words")]
        lb = PN(type=NodeType.BLOCK, roles={"statements": Role("statements")})
        cl.children["body"] = [lb]
        ca = PN(type=NodeType.ASSIGNMENT, roles={"targets": Role("targets"), "value": Role("value")})
        ca.children["targets"] = [PN(type=NodeType.INDEX_ACCESS, roles={"object": Role("object"), "index": Role("index")})]
        lb.children["statements"] = [ca]
        rt = PN(type=NodeType.RETURN_STMT, roles={"value": Role("value")})
        rt.children["value"] = []
        bd = PN(type=NodeType.BLOCK, roles={"statements": Role("statements")})
        bd.children["statements"] = [ra, sa, cl, rt]
        fn = PN(type=NodeType.FUNCTION_DEF, roles={"name": Role("name"), "params": Role("params"), "body": Role("body")})
        fn.children["name"] = [PR(type=NodeType.VARIABLE, value=name)]
        fn.children["params"] = [PR(type=NodeType.VARIABLE, value="path", role="param")]
        fn.children["body"] = [bd]
        return fn


# ═══════════════════════════════════════════════════════════════════
# 2. SLOT FILLER: minták beillesztése a vázba
# ═══════════════════════════════════════════════════════════════════

class SimplePatternFactory:
    """
    Egyszerű minták generálása — a "kreativitás" magja.
    
    Amikor a DKA-nak nincs megfelelő klónozható mintája,
    itt generálunk egy újat a semmiből.
    
    Pl.: "guess == target" — nincs a gráfban, de fel tudjuk építeni.
    """
    
    @staticmethod
    def make_comparison(left_var: str, op: str, right_var: str) -> PatternNode:
        """Összehasonlítás: left op right (pl. guess == target)."""
        op_map = {
            "==": "Eq", "!=": "NotEq", "<": "Lt", "<=": "LtE",
            ">": "Gt", ">=": "GtE", "in": "In", "not in": "NotIn",
        }
        op_name = op_map.get(op, "Eq")
        
        comp = PatternNode(type=NodeType.COMPARISON,
            roles={
                "left": Role("left"),
                "ops": Role("ops"),
                "comparators": Role("comparators"),
            })
        comp.children["left"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=left_var)]
        comp.children["ops"] = [
            PrimitiveNode(type=NodeType.OPERATOR, value=op_name, role="operator")]
        comp.children["comparators"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=right_var)]
        return comp
    
    @staticmethod
    def make_func_call(name: str, *args) -> PatternNode:
        """Függvényhívás: name(arg1, arg2, ...)."""
        call = PatternNode(type=NodeType.FUNCTION_CALL,
            roles={
                "func": Role("func"),
                "args": Role("args"),
            })
        call.children["func"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=name)]
        call.children["args"] = []
        for a in args:
            if isinstance(a, int):
                call.children["args"].append(
                    PrimitiveNode(type=NodeType.LITERAL, value=str(a)))
            else:
                call.children["args"].append(
                    PrimitiveNode(type=NodeType.LITERAL, value=f'"{a}"'))
        return call
    
    @staticmethod
    def make_assign(target: str, value_node: BaseNode) -> PatternNode:
        """Értékadás: target = value."""
        assign = PatternNode(type=NodeType.ASSIGNMENT,
            roles={"targets": Role("targets"), "value": Role("value")})
        assign.children["targets"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value=target)]
        assign.children["value"] = [value_node]
        return assign
    
    @staticmethod
    def make_return(value: str = None) -> PatternNode:
        """Return utasítás."""
        ret = PatternNode(type=NodeType.RETURN_STMT,
            roles={"value": Role("value")})
        if value:
            ret.children["value"] = [
                PrimitiveNode(type=NodeType.VARIABLE, value=value)]
        else:
            # Ne legyen üres a children (különben placeholder-nek hiszi)
            ret.children["value"] = []
        return ret
    
    @staticmethod
    def make_print(*args: str) -> PatternNode:
        """Print függvényhívás."""
        call = PatternNode(type=NodeType.FUNCTION_CALL,
            roles={"func": Role("func"), "args": Role("args")})
        call.children["func"] = [
            PrimitiveNode(type=NodeType.VARIABLE, value="print")]
        call.children["args"] = [
            PrimitiveNode(type=NodeType.LITERAL, value=f'"{a}"')
            for a in args]
        return call

class SlotFiller:
    """
    Váz kitöltése: minden slotba a legjobb minta keresése + illesztés.
    """
    
    def __init__(self, graph: HypergraphV2, semantics: SemanticIndex):
        self.graph = graph
        self.semantics = semantics
        self.engine = InferenceEngineV2(graph)
        self.factory = SimplePatternFactory()
        self._func_call_count = 0  # Hányadik FUNCTION_CALL-t töltjük
    
    def fill(self, scaffold: PatternNode, goal: str) -> PatternNode:
        """Váz kitöltése a cél alapján."""
        self._scaffold_vars = self._find_scaffold_vars(scaffold)
        self._func_call_count = 0
        self._fill_node(scaffold, goal, 0)
        return scaffold
    
    def _find_scaffold_vars(self, node: BaseNode, parent_role: str = "") -> list[str]:
        """Változók gyűjtése a scaffoldból (kivéve függvénynevet)."""
        vars_found = []
        if isinstance(node, PrimitiveNode):
            if (node.type == NodeType.VARIABLE and parent_role != "name" 
                and node.role != "name"):
                vars_found.append(node.value)
        elif isinstance(node, PatternNode):
            for role, children in node.children.items():
                for child in children:
                    vars_found.extend(self._find_scaffold_vars(child, role))
        return list(set(vars_found))
    
    def _fill_node(self, node: BaseNode, goal: str, depth: int):
        """Rekurzív kitöltés: minden üres/placeholder részt keres."""
        if depth > 20:
            return
        
        if isinstance(node, PatternNode):
            # 1. ELŐSZÖR: speciális kezelés (IF_STATEMENT, COMPARISON)
            if node.type == NodeType.IF_STATEMENT:
                cond = node.children.get("condition", [None])[0]
                if cond and isinstance(cond, PatternNode) and cond.type == NodeType.COMPARISON:
                    self._fill_comparison(cond, goal)
                # Töltsük ki az IF body-kat
                self._fill_if_bodies(node, goal)
            
            # 2. AZUTÁN: general placeholder kitöltés
            for role, children in node.children.items():
                for i, child in enumerate(children):
                    is_empty_block = (isinstance(child, PatternNode) and 
                                     child.type == NodeType.BLOCK and
                                     not any(child.children.get(r, []) 
                                            for r in child.children))
                    is_empty_pattern = (isinstance(child, PatternNode) and 
                                       not child.children and
                                       child.type not in (NodeType.BLOCK,))
                    
                    if is_empty_block:
                        pass
                    elif is_empty_pattern:
                        if child.type == NodeType.FUNCTION_CALL:
                            replacement = self._generate_func_call(role, goal)
                        else:
                            replacement = self._find_best_for_type(child.type, goal)
                        if replacement:
                            children[i] = replacement
                    else:
                        self._fill_node(child, goal, depth + 1)
                
                # FunctionCall "func" slot
                if role == "func" and children and isinstance(children[0], PrimitiveNode):
                    if hasattr(children[0], 'type') and children[0].type == NodeType.VARIABLE:
                        func_name = self._find_func_for_goal(goal, role)
                        if func_name:
                            children[0].value = func_name
    
    def _find_best_for_type(self, ntype: NodeType, goal: str) -> Optional[PatternNode]:
        """Adott típushoz a legjobb minta keresése."""
        # Próbáljunk szemantikus keresést
        sr = self.semantics.search_by_text(goal, top_k=3)
        for r in sr:
            pid = r["id"]
            p = self.graph.patterns.get(pid)
            if p and isinstance(p, PatternNode) and p.type == ntype:
                return self.engine._clone_pattern(p)
        
        # Ha nincs szemantikus, bármelyik ilyen típusú
        cand = self.graph.find_by_type(ntype)
        if cand and isinstance(cand[0], PatternNode):
            return self.engine._clone_pattern(cand[0])
        
        return None
    
    def _find_func_for_goal(self, goal: str, role: str) -> Optional[str]:
        """Célhoz illő függvénynév keresése."""
        sr = self.semantics.search_by_text(goal, top_k=3)
        for r in sr:
            if r["type"] == "FUNCTION_DEF":
                return r.get("name", "")
        return None
    
    def _generate_func_call(self, role: str, goal: str) -> Optional[PatternNode]:
        """Függvényhívás generálása a szerepkör alapján.
        Az első hívás = random, a második = input."""
        self._func_call_count += 1
        goal_lower = goal.lower()
        
        # 1. hívás: random.randint (target kezdőérték)
        if self._func_call_count == 1 and any(w in goal_lower 
            for w in ["random", "guess", "game", "number"]):
            return self.factory.make_func_call("random.randint", 1, 100)
        
        # 2. hívás: input() (játékos tippje)
        if self._func_call_count == 2:
            return self.factory.make_func_call("input")
        
        # Fájl olvasás
        if any(w in goal_lower for w in ["file", "read", "open"]):
            return self.factory.make_func_call("open", "path")
        
        # Általános: szemantikus keresés
        sr = self.semantics.search_by_text(goal, top_k=5)
        for r in sr:
            if r["type"] == "FUNCTION_CALL":
                pid = r["id"]
                p = self.graph.patterns.get(pid)
                if p:
                    return self.engine._clone_pattern(p)
        
        return None
    
    def _fill_if_bodies(self, if_node: PatternNode, goal: str):
        """IF body-k kitöltése tartalommal."""
        body = if_node.children.get("body", [None])[0]
        orelse = if_node.children.get("orelse", [])
        
        goal_lower = goal.lower()
        
        # IF body (találat): print + return
        if body and isinstance(body, PatternNode):
            stmts = body.children.get("statements", [])
            if not stmts:
                body.children["statements"] = [
                    self.factory.make_func_call("print", "Correct!"),
                    self.factory.make_return(),
                ]
        
        # ELSE body (nem találat): print hint + continue
        if orelse:
            else_body = orelse[0] if isinstance(orelse[0], PatternNode) else None
            if else_body and isinstance(else_body, PatternNode):
                stmts = else_body.children.get("statements", [])
                if not stmts:
                    # Próbáljunk értelmes hintet adni
                    hint = "Try again!"
                    if "guess" in goal_lower or "number" in goal_lower:
                        hint = "Too high or too low!"
                    elif "greater" in goal_lower:
                        hint = "Too low!"
                    elif "less" in goal_lower:
                        hint = "Too high!"
                    else:
                        hint = "Wrong! Try again."
                    else_body.children["statements"] = [
                        self.factory.make_func_call("print", hint),
                    ]
    
    def _fill_comparison(self, comp: PatternNode, goal: str):
        """Összehasonlítás kitöltése a cél alapján.
        Ahelyett, hogy bubble_sort-ból klónoznánk, generáljuk a megfelelőt."""
        # Scaffold változókból: guess == target, vagy hasonló
        # Keressünk 2 változót a scaffoldban
        vars = self._find_scaffold_vars(comp) or self._scaffold_vars
        
        # Ha nincs elég változó, próbáljunk a célból
        if not vars:
            vars = ["x", "y"]
        
        # Válasszunk 2 változót (az utolsó 2-t, ha van)
        if len(vars) >= 2:
            left = vars[-2]
            right = vars[-1]
        elif len(vars) == 1:
            left = vars[0]
            right = "0"
        else:
            left = "x"
            right = "y"
        
        # Döntsük el az operátort a cél alapján
        op = "=="
        if "greater" in goal or "nagyobb" in goal or ">" in goal:
            op = ">"
        elif "less" in goal or "kisebb" in goal or "<" in goal:
            op = "<"
        
        new_comp = self.factory.make_comparison(left, op, right)
        comp.children = new_comp.children


# ═══════════════════════════════════════════════════════════════════
# 3. STRUCTURED COMPOSER: a teljes folyamat
# ═══════════════════════════════════════════════════════════════════

class StructuredComposer:
    """
    Strukturált kompozíció: terv → váz → kitöltés → generálás.
    
    Ez a ReasoningEngine hiányzó része — ahelyett, hogy szövegeket
    fűzne össze, struktúra szinten dolgozik.
    """
    
    # Térkép
    SCAFFOLD_MAP = {
        "guess_game": ProgramScaffold.guess_game,
        "number_game": ProgramScaffold.guess_game,
        "word_count": ProgramScaffold.word_counter,
        "frequency": ProgramScaffold.word_counter,
        "data_process": ProgramScaffold.data_processor,
        "file_process": ProgramScaffold.data_processor,
    }
    
    def __init__(self, graph: HypergraphV2, generator: ConstructiveGenerator,
                 semantics: SemanticIndex):
        self.graph = graph
        self.generator = generator
        self.semantics = semantics
        self.slot_filler = SlotFiller(graph, semantics)
    
    def compose(self, plan_steps: list, goal: str) -> Optional[str]:
        """
        Terv lépésekből program összerakása.
        
        plan_steps: a ReasoningEngine által előállított lépések
        goal: az eredeti cél
        """
        # 1. Válasszunk vázat a cél alapján
        scaffold = self._select_scaffold(goal)
        
        if scaffold is None:
            # Ha nincs váz, próbáljunk egyszerűbb kompozíciót
            return self._simple_compose(plan_steps, goal)
        
        # 2. Töltsük ki a vázat
        filled = self.slot_filler.fill(scaffold, goal)
        
        # 3. Generáljunk kódot
        code = self.generator.generate(filled)
        
        # 4. Ellenőrizzük
        try:
            compile(code, "<composed>", "exec")
            return code
        except SyntaxError:
            # Ha hibás, próbáljuk egyszerűbben
            return self._simple_compose(plan_steps, goal)
    
    def _select_scaffold(self, goal: str) -> Optional[PatternNode]:
        """Célhoz illő váz kiválasztása."""
        goal_lower = goal.lower()
        
        # 1. Ismert váz kulcsszavak (szóhatárokkal)
        words = set(goal_lower.split())
        
        if words & {"guess", "game", "number", "tipp", "játék"}:
            name = self._generate_name(goal, "guess_game")
            return ProgramScaffold.guess_game(name)
        
        if words & {"file", "read", "process", "csv", "fájl"}:
            name = self._generate_name(goal, "process")
            return ProgramScaffold.data_processor(name)
        
        if words & {"word", "frequency", "count", "szó", "gyakoriság"}:
            name = self._generate_name(goal, "word_frequency")
            return ProgramScaffold.word_counter(name)
        
        # 2. Szemantikus keresés
        sr = self.semantics.search_by_text(goal, top_k=1)
        if sr:
            r = sr[0]
            if r["type"] == "FUNCTION_DEF":
                name = r.get("name", "process")
                return ProgramScaffold.simple_function(name)
        
        return None
    
    def _generate_name(self, goal: str, default: str) -> str:
        """Függvénynév generálása a célból."""
        words = goal.lower().split()
        # Vegyük az első 2 értelmes szót
        good = [w for w in words if len(w) > 2 and w.isalpha()][:2]
        if good:
            return "_".join(good)
        return default
    
    def _simple_compose(self, plan_steps: list, goal: str) -> Optional[str]:
        """Egyszerű kompozíció: ha nincs váz, szemantikus keresés."""
        sr = self.semantics.search_by_text(goal, top_k=3)
        for r in sr:
            if r["type"] == "FUNCTION_DEF":
                pid = r["id"]
                p = self.graph.patterns.get(pid)
                if p:
                    code = self.generator.generate(p)
                    try:
                        compile(code, "<simple>", "exec")
                        return code
                    except SyntaxError:
                        pass
        
        # Utolsó esély: bármi
        if sr:
            pid = sr[0]["id"]
            p = self.graph.patterns.get(pid)
            if p:
                return self.generator.generate(p)
        
        return None


# ═══════════════════════════════════════════════════════════════════
# TESZT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    
    from hypergraph_v2 import HypergraphV2
    from constructive_generator import ConstructiveGenerator
    from semantic_layer import SemanticIndex
    
    if not os.path.exists("dka_trained_500.json"):
        print("Futtasd: python mass_train_v2.py")
        sys.exit(1)
    
    g = HypergraphV2.from_json_file("dka_trained_500.json")
    sem = SemanticIndex(g)
    sem.index_all()
    gen = ConstructiveGenerator(g)
    composer = StructuredComposer(g, gen, sem)
    
    print("=== STRUKTURÁLT KOMPOZÍCIÓ ===")
    
    for goal in ["guess the number", "process a file", "sort array"]:
        print(f"\n--- '{goal}' ---")
        code = composer.compose([], goal)  # plan_steps üres, composer maga dönt
        if code:
            print(code)
            try:
                compile(code, "<test>", "exec")
                print("  [OK] Valid Python!")
            except SyntaxError as e:
                print(f"  [HIBA] {e}")
        else:
            print("  (nincs válasz)")
