"""
DKA V3 — Planner
================
A tervező réteg. Kap egy feladatot (természetes nyelven),
szétbontja részcélokra, minden részcélhoz megtalálja a megfelelő
fogalmakat a ConceptGraph-ban, és egy tervet készít belőlük.

A terv nem kód! A terv egy fogalmi folyamatábra:
  "szűrd ki a páros számokat" →
  [gyűjtemény] → [bejárás] → [feltétel: páros] → [szűrés] → [gyűjtemény]

Ezt a tervet később a Generator alakítja át konkrét kóddá.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Optional
from concept_graph import ConceptGraph, Concept, RelationType


@dataclass
class PlanStep:
    """Egy lépés a tervben."""
    action: str                # Mit kell csinálni
    target: str = ""           # Min dolgozunk
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    children: list[PlanStep] = field(default_factory=list)
    description: str = ""
    completed: bool = False
    file: str = ""  # Melyik fájlba kerül (üres = main.py)
    _id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


@dataclass
class Plan:
    """Egy teljes terv. Tartalmazza a lépéseket és a célt."""
    goal: str
    steps: list[PlanStep] = field(default_factory=list)
    input_concepts: list[str] = field(default_factory=list)
    output_concept: str = ""
    
    def summary(self) -> str:
        """Terv szöveges összefoglalója."""
        lines = [f"Terv: {self.goal}"]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"  {i}. {step.description or step.action}")
            for child in step.children:
                lines.append(f"     - {child.description or child.action}")
        lines.append(f"  Kimenet: {self.output_concept}")
        return "\n".join(lines)


class GoalParser:
    """
    Feladat szöveg → fogalmi elemek.
    
    Nem tokenizál! Fogalmakat keres a szövegben, és
    kapcsolatokat épít közöttük.
    """
    
    def __init__(self, graph: ConceptGraph):
        self.graph = graph
        
        # Ismert feladattípusok és a hozzájuk tartozó fogalmak
        self._task_patterns = {
            # Adatműveletek
            "szűr": ("szűrés", "gyűjtemény"),
            "szurd": ("szűrés", "gyűjtemény"),
            "filter": ("szűrés", "gyűjtemény"),
            "válogat": ("szűrés", "gyűjtemény"),
            "rendez": ("rendezés", "gyűjtemény"),
            "sort": ("rendezés", "gyűjtemény"),
            "transzformál": ("transzformáció", "gyűjtemény"),
            "map": ("transzformáció", "gyűjtemény"),
            "összegez": ("összegzés", "gyűjtemény"),
            "sum": ("összegzés", "gyűjtemény"),
            
            # HTML
            "űrlap": ("űrlap", "weblap"),
            "urlap": ("űrlap", "weblap"),
            "urlappal": ("űrlap", "weblap"),
            "form": ("űrlap", "weblap"),
            "input": ("input_mező", "űrlap"),
            "gomb": ("gomb", "űrlap"),
            "button": ("gomb", "űrlap"),
            "weblap": ("weblap", None),
            "html": ("weblap", None),
            "oldal": ("weblap", None),
            "oldalt": ("weblap", None),
            "page": ("weblap", None),
            "cím": ("cím", "weblap"),
            "cim": ("cím", "weblap"),
            "cimmel": ("cím", "weblap"),
            "bekezdés": ("bekezdés", "weblap"),
            "bekezdes": ("bekezdés", "weblap"),
            "bekezdessel": ("bekezdés", "weblap"),
            
            # ÚJ HTML elemek
            "kép": ("kép", "weblap"),
            "keppel": ("kép", "weblap"),
            "tablazat": ("táblázat", "weblap"),
            "tablazattal": ("táblázat", "weblap"),
            "link": ("link", "weblap"),
            "linkkel": ("link", "weblap"),
            "menu": ("menü", "weblap"),
            "menüvel": ("menü", "weblap"),
            "stilus": ("stílus", "weblap"),
            "stilussal": ("stílus", "weblap"),
            "fejlec": ("fejléc", "weblap"),
            "fejleccel": ("fejléc", "weblap"),
            "lablec": ("lábléc", "weblap"),
            "labfejlec": ("weblap", None),
            
            # Adatműveletek (új)
            "legkisebb": ("minimum", "gyűjtemény"),
            "legnagyobb": ("maximum", "gyűjtemény"),
            "minimum": ("minimum", "gyűjtemény"),
            "maximum": ("maximum", "gyűjtemény"),
            "átlag": ("átlag", "gyűjtemény"),
            "atlag": ("átlag", "gyűjtemény"),
            "atlagot": ("átlag", "gyűjtemény"),
            "fordíts": ("fordítás", "gyűjtemény"),
            "fordits": ("fordítás", "gyűjtemény"),
            "forditsd": ("fordítás", "gyűjtemény"),
            "fordítsd": ("fordítás", "gyűjtemény"),
            "megfordít": ("fordítás", "gyűjtemény"),
            "számlál": ("megszámlálás", "gyűjtemény"),
            "szamlal": ("megszámlálás", "gyűjtemény"),
            "számláld": ("megszámlálás", "gyűjtemény"),
            "szamlald": ("megszámlálás", "gyűjtemény"),
            "számold": ("megszámlálás", "gyűjtemény"),
            "szamold": ("megszámlálás", "gyűjtemény"),
            "első": ("első", "gyűjtemény"),
            "elso": ("első", "gyűjtemény"),
            "elsö": ("első", "gyűjtemény"),
            "vedd": ("első", "gyűjtemény"),
            "vond": ("átlag", "gyűjtemény"),
            "kivon": ("átlag", "gyűjtemény"),
            "vesz": ("első", "gyűjtemény"),
            
            # Adat (NE gyűjtemény — a célpontok máshogy jönnek)
            "lista": (None, "gyűjtemény"),
            "listát": (None, "gyűjtemény"),
            "listat": (None, "gyűjtemény"),
            "listabol": (None, "gyűjtemény"),
            "tömb": (None, "gyűjtemény"),
            "array": (None, "gyűjtemény"),
            "elem": (None, "gyűjtemény"),
            "elemet": (None, "gyűjtemény"),
            "szótár": (None, "szótár"),
            "dict": (None, "szótár"),
            
            # PORFOLIO & BEMUTATKOZAS
            "portfolio": ("weblap", None),
            "portfolió": ("weblap", None),
            "portfolioweboldalt": ("weblap", None),
            "bemutatkozás": ("bekezdés", "weblap"),
            "bemutatkozas": ("bekezdés", "weblap"),
            "bemutatkozo": ("bekezdés", "weblap"),
            "szolgáltatás": ("kártya", "weblap"),
            "szolgaltatas": ("kártya", "weblap"),
            "kártya": ("kártya", "weblap"),
            "kartyat": ("kártya", "weblap"),
            "card": ("kártya", "weblap"),
            "kapcsolatfelveteli": ("űrlap", "weblap"),
            "kapcsolat": ("űrlap", "weblap"),
            "contact": ("űrlap", "weblap"),
            "név": ("input_mező", "űrlap"),
            "nev": ("input_mező", "űrlap"),
            "nevet": ("input_mező", "űrlap"),
            "email": ("email_input", "űrlap"),
            "jelszó": ("password_input", "űrlap"),
            "jelszo": ("password_input", "űrlap"),
            "üzenet": ("textarea", "űrlap"),
            "uzenet": ("textarea", "űrlap"),
            "message": ("textarea", "űrlap"),
            "textarea": ("textarea", "űrlap"),
            "navigáció": ("menü", "weblap"),
            "navigacio": ("menü", "weblap"),
            "menü": ("menü", "weblap"),
            "navigaciot": ("menü", "weblap"),

            # ===== PYTHON MINTÁK (50+) =====
            "fuggveny": ("függvény", None),
            "fuggvenyt": ("függvény", None),
            "fuggvennyel": ("függvény", None),
            "function": ("függvény", None),
            "osztaly": ("osztály", None),
            "osztalyt": ("osztály", None),
            "class": ("osztály", None),
            "metodus": ("metódus", None),
            "metodussal": ("metódus", None),
            "method": ("metódus", None),
            "lambda": ("lambda", None),
            "async": ("async_függvény", None),
            "await": ("await", None),
            "dekorator": ("dekorátor", None),
            "decorator": ("dekorátor", None),
            "generator": ("generátor", None),
            "yield": ("generátor", None),
            "cache": ("cache", None),
            "kontextus": ("kontextus_kezelő", None),
            "context": ("kontextus_kezelő", None),
            "try": ("try_catch", None),
            "kivetel": ("kivétel", None),
            "exception": ("kivétel", None),
            "hiba": ("try_catch", None),
            "fajl": ("fájl_olvas", None),
            "fajlt": ("fájl_olvas", None),
            "file": ("fájl_olvas", None),
            "csv": ("csv_olvasás", None),
            "json": ("json_olvasás", None),
            "random": ("véletlen", None),
            "property": ("property_getter", None),
            "getter": ("property_getter", None),
            "setter": ("property_setter", None),
            "enum": ("enum_osztály", None),
            "dataclass": ("adat_osztály", None),
            "import": ("import", None),
            "from": ("from_import", None),
            "comprehension": ("list_comprehension", None),
            "reduce": ("reduce_kifejezés", "gyűjtemény"),

            # ===== JAVASCRIPT MINTÁK (30+) =====
            "fetch": ("fetch_get", None),
            "api": ("fetch_get", None),
            "dom": ("dom_kiválasztás", None),
            "localstorage": ("localStorage_mentés", None),
            "settimeout": ("setTimeout", None),
            "setinterval": ("setInterval", None),
            "esemeny": ("dom_esemény", None),
            "event": ("dom_esemény", None),
            "validacio": ("űrlap_validáció", None),
            "animacio": ("animáció_indítás", None),
            "konzol": ("kiírás", None),
            "callback": ("függvény", None),
            "promise": ("async_fetch", None),

            # ===== KOMPLEX WEB MINTÁK (20+) =====
            "hero": ("hero", "weblap"),
            "jellemzo": ("jellemző", "weblap"),
            "jellemzok": ("jellemzők", "weblap"),
            "jellemzovel": ("jellemző", "weblap"),
            "statisztika": ("statisztika", "weblap"),
            "stat": ("stat", "weblap"),
            "arazas": ("árazás", "weblap"),
            "pricing": ("árazás", "weblap"),
            "faq": ("faq", "weblap"),
            "tabs": ("tabs", "weblap"),
            "modalis": ("modális", "weblap"),
            "modal": ("modális", "weblap"),
            "oldalsav": ("oldalsáv", "weblap"),
            "sidebar": ("oldalsáv", "weblap"),
            "csapat": ("csapat", "weblap"),
            "csapattag": ("csapattag", "weblap"),
            "idovonal": ("idővonal", "weblap"),
            "visszajelzes": ("visszajelzés", "weblap"),
            "tesztimonium": ("tesztimónium", "weblap"),
            "hirlevel": ("hírlevél", "weblap"),
            "newsletter": ("hírlevél", "weblap"),
            "kereso": ("kereső", "weblap"),
            "lapozo": ("lapozó", "weblap"),
            "haladassav": ("haladássáv", "weblap"),
            "progress": ("haladássáv", "weblap"),

            # ===== JÁTÉK MINTÁK (20+) =====
            "játék": ("játék", None),
            "jatekot": ("játék", None),
            "jatek": ("játék", None),
            "jatekkal": ("játék", None),
            "jatekban": ("játék", None),
            "jatekbol": ("játék", None),
            "jatekotol": ("játék", None),
            "akció": ("játék", None),
            "akcio": ("játék", None),
            "karakter": ("karakter", "játék"),
            "karakterrel": ("karakter", "játék"),
            "karaktert": ("karakter", "játék"),
            "jatekos": ("karakter", "játék"),
            "ellenseg": ("ellenség", "játék"),
            "ellenseggel": ("ellenség", "játék"),
            "ellenseget": ("ellenség", "játék"),
            "lövedék": ("lövedék", "játék"),
            "lovedek": ("lövedék", "játék"),
            "platform": ("platform", "játék"),
            "pont": ("pontszám", "játék"),
            "pontszam": ("pontszám", "játék"),
            "szint": ("szint", "játék"),
            "ütközés": ("ütközés", "játék"),
            "utkozes": ("ütközés", "játék"),
            "game": ("játék", None),
            "pygame": ("játék", None),
            "mozgas": ("karakter", "játék"),
            "ellensegek": ("ellenség", "játék"),
            "spawn": ("ellenség", "játék"),
            "ai": ("ellenség", "játék"),

            # ===== ALGORITMUSOK =====
            "buborek": ("buborékrendezés", "gyűjtemény"),
            "bubble": ("buborékrendezés", "gyűjtemény"),
            "gyorsrendez": ("gyorsrendezés", "gyűjtemény"),
            "quicksort": ("gyorsrendezés", "gyűjtemény"),
            "bineris": ("bináris_keresés", "gyűjtemény"),
            "binary": ("bináris_keresés", "gyűjtemény"),
            "graf": ("gráf_bejárás", None),
            "graph": ("gráf_bejárás", None),
            "bfs": ("gráf_bejárás", None),
            "legrovidebb": ("legrövidebb_út", None),
            "faktorialis": ("faktoriális", None),
            "faktoriális": ("faktoriális", None),
            "factorial": ("faktoriális", None),
            "fibonacci": ("fibonacci", None),
            "primteszt": ("prímteszt", None),
            "prime": ("prímteszt", None),
            "palindrom": ("palindrom", None),
        }
        
        # Tulajdonság kereső szavak
        self._property_patterns = {
            "páros": ("páros", "szám"),
            "paros": ("páros", "szám"),
            "páratlan": ("páratlan", "szám"),
            "paratlan": ("páratlan", "szám"),
            "even": ("páros", "szám"),
            "odd": ("páratlan", "szám"),
            "nagy": ("nagyobb", "szám"),
            "kis": ("kisebb", "szám"),
            "pozitív": ("pozitív", "szám"),
            "pozitiv": ("pozitív", "szám"),
            "negatív": ("negatív", "szám"),
            "negativ": ("negatív", "szám"),
        }
    
    def parse(self, text: str) -> dict:
        """
        Szöveg elemzése: kinyeri a feladat típusát, a célt, a feltételeket.
        Visszaad egy szótárat a feladat strukturált reprezentációjával.
        """
        text_lower = text.lower()
        
        result = {
            "raw": text,
            "actions": [],
            "targets": [],
            "properties": [],
            "constraints": [],
        }
        
        # Feladat típus keresése
        for word, (action, target) in self._task_patterns.items():
            if word in text_lower:
                entry = {"word": word, "action": action, "target": target}
                if entry not in result["actions"]:
                    result["actions"].append(entry)
        
        # Tulajdonságok keresése
        for word, (prop, domain) in self._property_patterns.items():
            if word in text_lower:
                result["properties"].append({"word": word, "prop": prop, "domain": domain})
        
        # Célpont keresése
        words = text_lower.split()
        for w in words:
            if w in self.graph.concepts:
                if w not in [a["word"] for a in result["actions"]]:
                    result["targets"].append(w)
        
        return result
    
    def is_action_word(self, word: str) -> bool:
        """Szó akciót jelöl?"""
        return word in self._task_patterns


class Planner:
    """
    A tervező. Feladat → részcélok → fogalmak → terv.
    
    Hogyan működik:
    1. GoalParser elemzi a szöveget
    2. Minden felismert akcióhoz keres fogalmakat a ConceptGraph-ban
    3. Összerakja a lépéseket: mi az input, mi a művelet, mi az output
    4. Ellenőrzi, hogy a lánc értelmes-e
    """
    
    def __init__(self, graph: ConceptGraph, parser: GoalParser = None):
        self.graph = graph
        self.parser = parser or GoalParser(graph)
    
    def plan(self, goal: str) -> Optional[Plan]:
        """
        Fő belépési pont. Feladat → Terv.
        Most már HIERARCHIKUS: a PART_OF kapcsolatokat követve
        egymásba ágyazza a lépéseket.
        """
        parsed = self.parser.parse(goal)
        
        if not parsed["actions"]:
            return None
        
        plan = Plan(goal=goal)
        
        # ── SZÁMOSSÁG DETEKTÁLÁS ──
        # "két input", "három gomb", "öt mező" → hány példány kell?
        quantities = {"két": 2, "ket": 2, "kettő": 2, "ketto": 2,
                     "három": 3, "harom": 3, "négy": 4, "negy": 4,
                     "öt": 5, "ot": 5, "hat": 6, "hét": 7, "het": 7,
                     "nyolc": 8, "kilenc": 9, "tíz": 10, "tiz": 10,
                     "egy": 1}
        # Minden action-hoz: hány példány kell?
        action_qty = {}  # action_name → quantity
        
        words = goal.lower().split()
        for i, w in enumerate(words):
            if w in quantities:
                qty = quantities[w]
                # A következő 1-3 szó között keresünk action-t
                for offset in range(1, min(4, len(words) - i)):
                    next_word = words[i + offset]
                    for pattern_word, (action_name, _) in self.parser._task_patterns.items():
                        if next_word == pattern_word or next_word.startswith(pattern_word):
                            if action_name is not None:
                                action_qty[action_name] = qty
                            break
                            break
                    # Ha nem találtuk action-ben, lehet hogy a következő szó
                    # maga a koncepció (pl. "két mező")
                    for concept_name in self.graph.concepts:
                        if next_word == concept_name.lower():
                            # Keressük, melyik action kapcsolódik ehhez a koncepcióhoz
                            for pattern_word, (action_name, _) in self.parser._task_patterns.items():
                                if action_name == concept_name:
                                    action_qty[action_name] = qty
                                    break
                            break
        
        # 1. Összegyűjtjük az akciókat (deduplikálva)
        action_map = {}  # action_name -> step
        seen_actions = set()

        # Ékezetmentesítő függvény a parse()-ban használatra
        import unicodedata
        def no_acc(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

        for action_info in parsed["actions"]:
            action_name = action_info["action"]
            if action_name is None or action_name in seen_actions:
                continue
            seen_actions.add(action_name)
            
            target = action_info["target"]
            action_concept = self.graph.get(action_name)
            if not action_concept:
                continue
            
            step = PlanStep(
                action=action_name,
                target=target or "",
                description=action_concept.description,
            )
            
            # Ha van számosság (pl. "két input"), tároljuk
            step_qty = action_qty.get(action_name, 1)
            
            # Célpont változónév a feladat szövegéből
            stop_words = {"a", "az", "egy", "es", "es", "azt", "hogy",
                         "ki", "fel", "le", "be", "meg", "el", "nem",
                         "is", "mert", "ha", "de", "s", "mint", "már",
                         "hoz", "hez", "höz", "nal", "nel", "ban", "ben",
                         "majd", "ami", "amit", "amely", "ahol",
                         "olyan", "ilyen", "ilyet", "olyat",
                         "tovabba", "továbbá", "viszont", "ezert"}
            goal_words = [w for w in goal.lower().split()
                         if w not in stop_words and len(w) > 2]
            noun = ""
            for i, w in enumerate(reversed(goal_words)):
                if not self.parser.is_action_word(w):
                    noun = w
                    break
            if noun and noun not in seen_actions:
                # Magyar toldalékok levágása a változónévből
                # Pl. "szamokat" → "szam", "listabol" → "lista", "mezokkel" → "mezo"
                import re
                # Több lépésben: először a leghosszabb toldalékokat
                for suffix in ["okkal", "ekkel", "okbol", "ekbol",
                              "okhoz", "ekhez", "okat", "eket",
                              "ok", "ek", "ot", "et", "at",
                              "bol", "bol", "bel", "rol", "rol",
                              "val", "vel", "nak", "nek",
                              "ban", "ben", "ra", "re",
                              "hoz", "hez", "hoz", "hez",
                              "nal", "nel", "tol", "tol",
                              "ig", "kent", "ert",
                              "t", "a", "e", "i"]:
                    if noun.endswith(suffix) and len(noun) > len(suffix) + 2:
                        noun = noun[:-len(suffix)]
                        # Ha a tő "b"-re végződött és a toldalék "ol" volt
                        # pl. "listabol" → töröljük "ol" → "listab" → "lista"
                        if noun.endswith("b"):
                            noun = noun[:-1]
                        break
                step.target = noun
            
            # REQUIRES kapcsolatok
            for rel in action_concept.relations:
                if rel.type == RelationType.REQUIRES:
                    step.inputs.append(rel.target_name)
            
            # PRODUCES kapcsolatok
            for rel in action_concept.relations:
                if rel.type == RelationType.PRODUCES:
                    step.outputs.append(rel.target_name)
            
            action_map[action_name] = step
            # Ha több példány kell, duplikáljuk a lépést
            if step_qty > 1:
                for extra in range(1, step_qty):
                    extra_step = PlanStep(
                        action=action_name,
                        target=f"{step.target or action_name}_{extra+1}",
                        description=action_concept.description,
                    )
                    # Ugyanazok a kapcsolatok
                    extra_step.inputs = list(step.inputs)
                    extra_step.outputs = list(step.outputs)
                    action_map[f"{action_name}_{extra}"] = extra_step
        
        # Property constraint-ek hozzáadása az első olyan lépéshez,
        # ami REQUIRES feltételt
        if parsed["properties"]:
            for step in action_map.values():
                if "feltétel" in step.inputs:
                    for prop in parsed["properties"]:
                        step.children.append(PlanStep(
                            action="feltétel",
                            target=prop["domain"],
                            description=f"{prop['prop']} {prop['domain']}",
                        ))
                    break
        
        # 2. Hierarchia építése PART_OF kapcsolatok alapján
        # Melyik action melyiknek a része? (tranzitív is!)
        child_to_parent = {}  # child_action -> parent_action
        for action_name, step in action_map.items():
            concept = self.graph.get(action_name)
            if not concept:
                continue
            for rel in concept.relations:
                if rel.type == RelationType.PART_OF:
                    parent_name = rel.target_name
                    if parent_name in action_map:
                        child_to_parent[action_name] = parent_name
                    else:
                        # Tranzitív keresés: a PART_OF célpont nem szerepel a
                        # feladatban, de lehet hogy Ő is PART_OF valaminek
                        # Pl. gomb → űrlap → weblap, de űrlap nincs a tervben
                        transitive = self._find_transitive_parent(
                            parent_name, action_map, seen=set()
                        )
                        if transitive:
                            child_to_parent[action_name] = transitive
        
        # 3. A hierarchia alapján rendezzük a lépéseket
        root_steps = []
        for action_name, step in action_map.items():
            if action_name not in child_to_parent:
                # Copy-k (action_N) és normál lépések is root-ba kerülnek
                root_steps.append(step)
        
        # Gyerekek hozzáadása a szülőkhöz
        for child_name, parent_name in child_to_parent.items():
            if parent_name in action_map and child_name in action_map:
                parent_step = action_map[parent_name]
                existing = [c for c in parent_step.children if c.action == child_name]
                if not existing:
                    child_step = action_map[child_name]
                    parent_step.children.append(child_step)
                    # Gyerek eltávolítása a root-ok közül (_id alapján!)
                    for i, rs in enumerate(root_steps):
                        if rs._id == child_step._id:
                            root_steps.pop(i)
                            break
        
        # 3.5. Függvény/Osztály body hierarchia építése
        # Ha "függvény" lépés van, a body műveletek (visszatérés, összegzés, kiírás)
        # legyenek a függvény gyerekei. + jobb név extraction.
        self._build_body_hierarchy(action_map, child_to_parent, goal)
        
        # Root steps újraszámolása a body hierarchia után
        root_steps = []
        for action_name, step in action_map.items():
            if action_name not in child_to_parent:
                root_steps.append(step)
        
        # 4. Output fogalom beállítása
        if root_steps:
            last = root_steps[-1]
            if last.outputs:
                plan.output_concept = last.outputs[-1]
            else:
                concept = self.graph.get(last.action)
                if concept:
                    for rel in concept.relations:
                        if rel.type == RelationType.PRODUCES:
                            plan.output_concept = rel.target_name
                            break
        
        plan.steps = root_steps
        
        # Input fogalmak a célpontokból
        if parsed["targets"]:
            plan.input_concepts = parsed["targets"]
        
        return plan
    
    def _find_transitive_parent(self, concept_name: str,
                                 action_map: dict, seen: set) -> Optional[str]:
        """Tranzitív PART_OF keresés: ha X PART_OF Y és Y PART_OF Z,
        és Z szerepel a tervben, akkor X gyereke Z-nek."""
        if concept_name in seen:
            return None
        seen.add(concept_name)

        concept = self.graph.get(concept_name)
        if not concept:
            return None

        for rel in concept.relations:
            if rel.type == RelationType.PART_OF:
                if rel.target_name in action_map:
                    return rel.target_name
                result = self._find_transitive_parent(rel.target_name, action_map, seen)
                if result:
                    return result
        return None

    def _build_body_hierarchy(self, action_map: dict, child_to_parent: dict, goal: str):
        """Függvények, osztályok és játékok body hierarchiájának építése."""
        goal_lower = goal.lower()
        words = goal_lower.split()

        # === JÁTÉK HIERARCHIA ===
        self._build_game_hierarchy(action_map, child_to_parent, goal_lower)

        # === FÜGGVÉNY BODY HIERARCHIA ===
        if "függvény" in action_map:
            func_step = action_map["függvény"]

            # Jobb név: a "fuggvenyt ami X" vagy "fuggveny ami X" X szava
            func_name = self._extract_function_name(goal_lower)
            if func_name:
                func_step.target = func_name

            # 1. ELŐSZÖR: description-based body (valós kifejezésekkel)
            import re
            if any(w in goal_lower for w in ["osszead", "osszeadas", "osszeadja"]):
                if not any(c.action == "visszatérés" for c in func_step.children) and \
                   "visszatérés" not in action_map:
                    func_step.children.append(PlanStep(action="visszatérés", target="érték",
                                                       description="a + b"))
            if any(w in goal_lower for w in ["szur", "szurd", "szűrj", "valogat"]):
                feltetel = "x % 2 == 0" if any(w in goal_lower for w in ["paros", "páros"]) else \
                           "x % 2 != 0" if any(w in goal_lower for w in ["paratlan", "páratlan"]) else "True"
                if not any(c.action == "visszatérés" for c in func_step.children):
                    func_step.children.append(PlanStep(action="visszatérés", target="lista",
                                                       description=f"[x for x in lista if {feltetel}]"))
            if any(w in goal_lower for w in ["rendez", "rendezd", "rendezi"]):
                if not any(c.action == "visszatérés" for c in func_step.children):
                    func_step.children.append(PlanStep(action="visszatérés", target="lista",
                                                       description="sorted(lista)"))
            if any(w in goal_lower for w in ["kiir", "kiirja", "ird"]):
                if not any(c.action == "kiírás" for c in func_step.children):
                    func_step.children.append(PlanStep(action="kiírás", target="szöveg",
                                                       description='print(szoveg)'))
            if any(w in goal_lower for w in ["megszamol", "megszamolja", "szamlal"]):
                if not any(c.action == "visszatérés" for c in func_step.children):
                    func_step.children.append(PlanStep(action="visszatérés", target="lista",
                                                       description="len(lista)"))
            if any(w in goal_lower for w in ["atlag", "atlagot", "atlagat", "átlag"]):
                if not any(c.action == "visszatérés" for c in func_step.children):
                    func_step.children.append(PlanStep(action="visszatérés", target="lista",
                                                       description="sum(lista)/len(lista)"))
            if any(w in goal_lower for w in ["masol", "masolas"]):
                if not any(c.action == "visszatérés" for c in func_step.children):
                    func_step.children.append(PlanStep(action="visszatérés", target="lista",
                                                       description="lista.copy()"))
            if any(w in goal_lower for w in ["keres", "keresd", "talal"]):
                if not any(c.action == "visszatérés" for c in func_step.children):
                    func_step.children.append(PlanStep(action="visszatérés", target="lista",
                                                       description="[x for x in lista if x == ertek]"))

            # 2. UTÁNA: action_map-ból származó body — SKIP ha már van visszatérés
            has_return = any(c.action == "visszatérés" for c in func_step.children)
            for body_action in ["visszatérés", "összegzés", "kiírás", "bejárás", "feltétel",
                                 "szűrés", "rendezés", "transzformáció", "megszámlálás",
                                 "lambda", "generátor", "minimum", "maximum", "átlag"]:
                if body_action in action_map and body_action not in child_to_parent:
                    if has_return and body_action != "kiírás":
                        del action_map[body_action]
                        continue  # Ha van return, a többi body felesleges
                    body_step = action_map[body_action]
                    if not any(c.action == body_action for c in func_step.children):
                        func_step.children.append(body_step)
                        child_to_parent[body_action] = "függvény"

        # === OSZTÁLY HIERARCHIA ===
        if "osztály" in action_map:
            class_step = action_map["osztály"]
            import re
            class_name = ""
            before_match = re.search(r'(\w+)\s+osztalye?t?', goal_lower)
            if before_match:
                cn = before_match.group(1)
                if cn not in ("a", "az", "egy", "es", "ami", "hogy", "ket", "harom", "negy", "ot", "ez", "azt"):
                    class_name = cn
            if not class_name:
                after_match = re.search(r'osztalye?t?\s+([a-záéíóöőúüű]+)', goal_lower)
                if after_match:
                    cn = after_match.group(1)
                    if cn not in ("a", "az", "egy", "es", "ami", "hogy", "ket", "harom", "negy", "ot"):
                        class_name = cn
            if class_name:
                class_step.target = class_name

            if "konstruktor" in action_map and "konstruktor" not in child_to_parent:
                constr_step = action_map["konstruktor"]
                if not any(c.action == "konstruktor" for c in class_step.children):
                    class_step.children.append(constr_step)
                    child_to_parent["konstruktor"] = "osztály"
            if "metódus" in action_map and "metódus" not in child_to_parent:
                method_step = action_map["metódus"]
                if not any(c.action == "metódus" for c in class_step.children):
                    class_step.children.append(method_step)
                    child_to_parent["metódus"] = "osztály"

    def _extract_function_name(self, goal: str) -> str:
        """Kivonja a függvény nevét a feladat szövegből.
        
        "keszits egy fuggvenyt ami osszead ket szamot" → "osszeadas"
        "fuggveny ami szuri a paros szamokat" → "szures"
        "fuggveny ami rendez egy listat" → "rendezes"
        """
        # Keressük a "fuggvenyt ami X" vagy "fuggveny ami X" mintát
        import re
        match = re.search(r'fuggvenye?t?\s+ami\s+(\w+)', goal)
        if match:
            verb = match.group(1)
            # Ige → főnév átalakítás
            name_map = {
                "osszead": "osszeadas", "osszeadja": "osszeadas",
                "szur": "szures", "szurd": "szures", "szűrj": "szures",
                "szuri": "szures", "szurje": "szures",
                "rendez": "rendezes", "rendezi": "rendezes", "rendezd": "rendezes",
                "kiir": "kiiras", "irj": "kiiras", "ird": "kiiras",
                "kiirja": "kiiras", "kiirni": "kiiras",
                "szamol": "szamolas", "kiszamol": "szamolas",
                "kiszamolja": "atlag", "kiszamitja": "atlag",
                "megszamol": "megszamlalas", "megszamolja": "megszamlalas",
                "megszam" : "megszamlalas",
                "general": "generalas", "naploz": "naplozas",
                "keres": "kereses", "talal": "kereses",
                "masol": "masolas", "valogat": "valogatas",
                "ellenoriz": "ellenorzes", "ell": "ellenorzes",
                "fordit": "forditas", "fordits": "forditas",
                "transzformal": "transzformacio",
                "csinal": "muvelet", "keszit": "letrehozas",
                "listaz": "listazas", "szamold": "szamolas",
                "szamold": "szamlalas", "szam": "szamolas",
                "olvas": "olvasas", "ir": "iras",
                "hozz": "hozzaadas", "vedd": "kivalasztas",
                "keresd": "kereses", "talald": "kereses",
                "modosits": "modositas", "valtoztass": "valtoztatas",
                "torolj": "torles", "adj": "hozzaadas",
            }
            return name_map.get(verb, verb + "_fv")
        return ""

    def _build_game_hierarchy(self, action_map: dict, child_to_parent: dict, goal: str):
        """Játék hierarchia építése. Alapértelmezett karakter/ellenség hozzáadás."""
        if "játék" not in action_map:
            return

        game_step = action_map["játék"]

        # Játék részei
        game_parts = ["karakter", "ellenség", "lövedék", "pontszám", "ütközés",
                      "platform", "akadály", "szint", "menü"]

        for part in game_parts:
            if part in action_map:
                part_step = action_map[part]
                if not any(c.action == part for c in game_step.children):
                    if not part_step.file:
                        part_step.file = {"karakter": "player.py", "ellenség": "enemy.py",
                                         "lövedék": "bullet.py", "pontszám": "score.py"}.get(part, "")
                    game_step.children.append(part_step)
                    child_to_parent[part] = "játék"

        # Alapértelmezett karakter és ellenség
        if not any(c.action == "karakter" for c in game_step.children):
            ps = PlanStep(action="karakter", target="player", file="player.py",
                          description="Játékos karakter")
            game_step.children.append(ps)
        if not any(c.action == "ellenség" for c in game_step.children):
            es = PlanStep(action="ellenség", target="enemy", file="enemy.py",
                          description="Ellenség")
            game_step.children.append(es)

        # Játék cím a goal-ból
        if "akció" in goal or "akcio" in goal:
            game_step.description = "Akció Játék"
        elif "platform" in goal:
            game_step.description = "Platform Játék"
        else:
            game_step.description = "Játék"

    def validate(self, plan: Plan) -> list[str]:
        """
        Terv ellenőrzése: minden lépés inputja rendelkezésre áll?
        Visszaadja a problémák listáját (üres = nincs probléma).
        """
        issues = []
        available = set(plan.input_concepts)
        
        for step in plan.steps:
            for inp in step.inputs:
                if inp not in available:
                    # Lehet, hogy a fogalom következtetésből elérhető?
                    found = False
                    for avail in available:
                        path = self.graph.shortest_path(avail, inp)
                        if path:
                            found = True
                            break
                    if not found:
                        issues.append(
                            f"Hiányzó input '{inp}' a '{step.action}' lépéshez"
                        )
            
            # Outputok hozzáadása az elérhetőkhöz
            for out in step.outputs:
                available.add(out)
        
        return issues
