"""
DKA V3 — SelfImprover V2
========================
Valódi önfejlesztő: nem csak hibákból tanul, hanem a meglévő
tudásából ÚJ fogalmakat, kapcsolatokat és template-eket fedez fel.

Hogyan?

1. ANALÓGIA: Ha X hasonló Y-hoz, és Y-nak van kapcsolata Z-vel,
   akkor X-nek is lehet kapcsolata Z-vel.

2. HIÁNYOSSÁG DETEKTÁLÁS: Ha egy fogalomnak feltűnően kevés
   kapcsolata van a hasonló fogalmakhoz képest, keresünk neki.

3. TEMPLATE FELFEDEZÉS: A meglévő template-ek mintájára
   újakat generál ismeretlen fogalmakhoz.

4. FOGALOM ÁLTALÁNOSÍTÁS: Ha több fogalomnak ugyanaz a
   kapcsolata, lehet hogy van egy közös ősük.

5. VISSZACSATOLÁS: Minden generálás után tanul — nem csak
   hibából, hanem SIKERBŐL is.
"""

from __future__ import annotations
from typing import Optional
from collections import Counter
import sys as _sys
from concept_graph import (
    ConceptGraph, Concept, Operation, Property,
    RelationType, ConceptRelation
)
from planner import Planner, Plan
from generator import Generator, LanguageDialect


class SelfImproverV2:
    """
    Önfejlesztő motor V2.
    
    Két üzemmód:
    1. Reaktív: hibákból tanul (mint V1)
    2. Proaktív: a meglévő tudásból új dolgokat fedez fel
    """
    
    def __init__(self, graph: ConceptGraph, planner: Planner, generator: Generator):
        self.graph = graph
        self.planner = planner
        self.generator = generator
        self.improvement_count = 0
        self.discoveries: list[str] = []
    
    # ══════════════════════════════════════════════════
    # 1. ANALÓGIA ALAPÚ FELFEDEZÉS
    # ══════════════════════════════════════════════════
    
    def discover_by_analogy(self) -> list[str]:
        """
        Analógia keresés: ha két fogalom hasonló, és az egyiknek
        van olyan kapcsolata, ami a másiknak nincs, javasoljuk.
        
        Pl.:
        - input_mezo PART_OF urlap
        - van "gomb" fogalom
        - gomb-nek nincs PART_OF kapcsolata urlap-pal
        - De: gomb HAS_PROPERTY kattinthato, input_mezo HAS_PROPERTY bevitel
        - Ha elég hasonló → gomb PART_OF urlap is!
        """
        findings = []
        concepts = list(self.graph.concepts.values())
        
        for a in concepts:
            for b in concepts:
                if a.name >= b.name:
                    continue  # Minden párt csak egyszer
                
                # Hasonlóság számítása: közös kapcsolatok / összes kapcsolat
                a_rels = {(r.type, r.target_name) for r in a.relations}
                b_rels = {(r.type, r.target_name) for r in b.relations}
                
                if not a_rels or not b_rels:
                    continue
                
                common = a_rels & b_rels
                similarity = len(common) / max(len(a_rels | b_rels), 1)
                
                if similarity >= 0.3:  # 30%+ hasonlóság
                    # A-nak van olyan kapcsolata, ami B-nek nincs?
                    for rel in a.relations:
                        key = (rel.type, rel.target_name)
                        if key not in b_rels:
                            # Lehet, hogy B-nek is kellene ez a kapcsolat?
                            target_concept = self.graph.get(rel.target_name)
                            if target_concept:
                                # Csak akkor adjuk hozzá, ha értelmes
                                self.graph.relate(
                                    b.name, rel.target_name, rel.type,
                                    strength=similarity * 0.5,  # Alacsonyabb biztonság
                                    description=f"Analógia alapján ({a.name} → {rel.target_name})"
                                )
                                findings.append(
                                    f"[ANALÓGIA] {b.name} {rel.type.name} {rel.target_name} "
                                    f"(hasonló: {a.name}, hasonlóság: {similarity:.0%})"
                                )
        
        self.discoveries.extend(findings)
        return findings
    
    # ══════════════════════════════════════════════════
    # 2. HIÁNYOSSÁG DETEKTÁLÁS
    # ══════════════════════════════════════════════════
    
    def detect_gaps(self) -> list[str]:
        """
        Hiányzó kapcsolatok keresése.
        
        Ha egy fogalomnak nagyon kevés kapcsolata van a többihez képest,
        keressünk neki újakat a meglévő tudás alapján.
        
        Pl.:
        - "bekezdes" be lett töltve, de nincs kapcsolata
        - De van "cim" ami PART_OF "weblap"
        - "bekezdes" és "cim" hasonló (mindkettő szöveges elem a weboldalon)
        - → "bekezdes" PART_OF "weblap"
        """
        findings = []
        
        for concept in self.graph.concepts.values():
            if len(concept.relations) == 0:
                # Ennek a fogalomnak SEMMI kapcsolata nincs!
                # Keressünk hasonló fogalmakat, amiknek VAN
                best_match = None
                best_sim = 0
                
                for other in self.graph.concepts.values():
                    if other.name == concept.name or len(other.relations) == 0:
                        continue
                    
                    # Név hasonlóság? (pl. "cim" és "bekezdes" — mindkettő web elem)
                    # Leírás hasonlóság?
                    desc_words_a = set(concept.description.lower().split())
                    desc_words_b = set(other.description.lower().split())
                    desc_overlap = len(desc_words_a & desc_words_b) / max(len(desc_words_a | desc_words_b), 1)
                    
                    if desc_overlap > best_sim:
                        best_sim = desc_overlap
                        best_match = other
                
                if best_match and best_sim > 0:
                    # Másoljuk a legjobban hasonló fogalom kapcsolatait
                    for rel in best_match.relations:
                        # Csak akkor, ha a cél fogalom létezik
                        if self.graph.get(rel.target_name):
                            self.graph.relate(
                                concept.name, rel.target_name, rel.type,
                                strength=0.3,
                                description=f"Hiánypótlás ({best_match.name} alapján)"
                            )
                            findings.append(
                                f"[HIÁNYPÓTLÁS] {concept.name} {rel.type.name} {rel.target_name} "
                                f"(alapján: {best_match.name})"
                            )
        
        self.discoveries.extend(findings)
        return findings
    
    # ══════════════════════════════════════════════════
    # 3. TEMPLATE FELFEDEZÉS
    # ══════════════════════════════════════════════════
    
    def discover_templates(self) -> list[str]:
        """
        Hiányzó template-ek automatikus generálása.
        
        Minden nyelv dialektusában megnézzük, hogy minden fogalomhoz
        tartozik-e template. Ahol hiányzik, ott a fogalom nevéből
        generálunk egy egyszerű template-et.
        """
        findings = []
        
        for lang_name, dialect in self.generator.dialects.items():
            for concept_name in self.graph.concepts:
                if not dialect.get_template(concept_name):
                    # Nincs template ehhez a fogalomhoz!
                    # Generáljunk egyet a fogalom nevéből
                    if lang_name == "html":
                        # HTML: <div class="fogalom_neve">...</div>
                        template = f"<div class=\"{concept_name}\">{{children}}</div>"
                    elif lang_name in ("python", "javascript"):
                        # Python/JS: # concept_name vagy // concept_name
                        comment_char = "#" if lang_name == "python" else "//"
                        template = f"{comment_char} {concept_name}: {{body}}"
                    else:
                        template = f"<!-- {concept_name} -->"
                    
                    dialect.map(concept_name, template)
                    findings.append(
                        f"[TEMPLATE] {lang_name}: '{concept_name}' → {template}"
                    )
        
        self.discoveries.extend(findings)
        return findings
    
    # ══════════════════════════════════════════════════
    # 4. FOGALOM ÁLTALÁNOSÍTÁS
    # ══════════════════════════════════════════════════
    
    def generalize(self) -> list[str]:
        """
        Általánosítás: ha több fogalomnak ugyanaz a kapcsolata,
        lehet hogy van egy közös ősük.
        
        Pl.:
        - input_mezo PART_OF urlap
        - gomb PART_OF urlap
        - Van "urlap" fogalom
        - De nincs "urlap_alkatresz" ős
        - → Lehet hogy kellene egy "urlap_alkatresz" IS_A kapcsolat
        """
        findings = []
        
        # Csoportosítsuk a kapcsolatokat típus + cél szerint
        relation_groups = {}  # (type, target) → [source_names]
        
        for concept in self.graph.concepts.values():
            for rel in concept.relations:
                key = (rel.type.name, rel.target_name)
                if key not in relation_groups:
                    relation_groups[key] = []
                relation_groups[key].append(concept.name)
        
        # Ha egy kapcsolathoz 2+ forrás tartozik, lehet hogy kell egy ős
        for (rel_type, target), sources in relation_groups.items():
            if len(sources) >= 2:
                # Minden forrás ugyanazt a kapcsolatot használja
                # Nézzük, van-e közös IS_A ősük
                common_parents = None
                for source in sources:
                    concept = self.graph.get(source)
                    if not concept:
                        continue
                    parents = {
                        r.target_name for r in concept.relations
                        if r.type == RelationType.IS_A
                    }
                    if common_parents is None:
                        common_parents = parents
                    else:
                        common_parents &= parents
                
                if common_parents is None or len(common_parents) == 0:
                    # Nincs közös ős! Lehet hogy kellene egy.
                    # De ezt most csak naplózzuk — a felhasználó dönt
                    findings.append(
                        f"[ÁLTALÁNOSÍTÁS] {sources} mind {rel_type.lower()} {target}, "
                        f"de nincs közös ősük"
                    )
        
        self.discoveries.extend(findings)
        return findings
    
    # ══════════════════════════════════════════════════
    # 5. SIKERBŐL TANULÁS — ÚJ SZABÁLYOK FELFEDEZÉSE
    # ══════════════════════════════════════════════════
    
    def learn_from_success(self, goal: str, plan: Plan, language: str):
        """
        Ha sikeresen generáltunk kódot, elemzi a folyamatot és
        új szabályokat von ki belőle.
        
        Amit tanul:
        1. Új szó → akció kapcsolatok (pl. "csinálj" → weblap)
        2. Új szó → koncepció kapcsolatok (pl. "weboldal" → weblap)
        3. Sikeres szó-kombinációk megerősítése
        4. Ha ismeretlen szavak voltak a goal-ban, felveszi őket
        """
        goal_lower = goal.lower()
        words = goal_lower.split()
        
        # 1. Melyik szavak vezettek action-ökhöz?
        used_words = set()
        def collect_actions(step):
            # action neve a szó amihez tartozik
            for w in words:
                if w.startswith(step.action[:3]) or step.action.startswith(w[:3]):
                    used_words.add(w)
            for c in step.children:
                collect_actions(c)
        
        for step in plan.steps:
            collect_actions(step)
        
        # 2. Ismeretlen szavak → új szabály javaslat
        parser = self.planner.parser
        new_patterns = 0
        for word in words:
            if len(word) < 3:
                continue
            # Ha ez a szó NEM ismert action, DE sikeresen
            # egy action-höz vezetett a tervben
            if not parser.is_action_word(word):
                # Keressük, melyik action-höz kapcsolódhat
                for step in plan.steps:
                    # Név hasonlóság: "weboldal" → "weblap"
                    similarity = self._word_similarity(word, step.action)
                    if similarity > 0.3:
                        # Új szó → action szabály tanulása
                        # Hozzáadjuk a parser _task_patterns-hez
                        parser._task_patterns[word] = (step.action, "")
                        self.discoveries.append(
                            f"[TANULÁS] \"{word}\" → {step.action} "
                            f"(hasonlóság: {similarity:.0%})"
                        )
                        new_patterns += 1
                        break
        
        # 3. Megerősítjük a használt fogalmak kapcsolatait
        def strengthen(step):
            concept = self.graph.get(step.action)
            if concept:
                for rel in concept.relations:
                    rel.strength = min(1.0, rel.strength + 0.05)
            for child in step.children:
                strengthen(child)
        
        for step in plan.steps:
            strengthen(step)
        
        self.improvement_count += 1
        
        if new_patterns > 0:
            self.discoveries.append(
                f"[TANULÁS] {new_patterns} új szó→akció szabály a '{goal}' feladatból"
            )
    
    def _word_similarity(self, word_a: str, word_b: str) -> float:
        """
        Két szó hasonlósága.
        Szótagszint: "weboldal" vs "weblap" → "web" közös
        """
        a = word_a.lower().strip()
        b = word_b.lower().strip()
        
        if a == b:
            return 1.0
        
        # Közös prefix
        common_prefix = 0
        for i in range(min(len(a), len(b))):
            if a[i] == b[i]:
                common_prefix += 1
            else:
                break
        
        if common_prefix >= 2:
            return common_prefix / max(len(a), len(b))
        
        # Közös karakterek
        common = sum(1 for c in a if c in b)
        return common / max(len(a), len(b)) if max(len(a), len(b)) > 0 else 0
    
    # ══════════════════════════════════════════════════
    # 6. TELJES FELFEDEZÉSI CIKLUS
    # ══════════════════════════════════════════════════
    
    def discover_all(self) -> list[str]:
        """
        Teljes felfedezési ciklus futtatása.
        Minden módszert meghív, és visszaadja az összes felfedezést.
        """
        all_findings = []
        
        all_findings.extend(self.discover_by_analogy())
        all_findings.extend(self.detect_gaps())
        all_findings.extend(self.discover_templates())
        all_findings.extend(self.generalize())
        
        return all_findings
    
    # ══════════════════════════════════════════════════
    # TELJES CIKLUS
    # ══════════════════════════════════════════════════
    
    def run(self, goal: str, language: str = "python",
            max_attempts: int = 3) -> tuple[Optional[str], list[str]]:
        """
        Teljes ciklus: tervez → generál → ellenőriz → felfedez → javít → újra.
        """
        log = []
        
        # Először: felfedezés (hátha van új tudás)
        discoveries = self.discover_all()
        if discoveries:
            log.append(f"Felfedezések a meglévő tudásból:")
            for d in discoveries[:5]:
                log.append(f"  {d}")
        
        for attempt in range(1, max_attempts + 1):
            log.append(f"[{attempt}/{max_attempts}] {goal}")
            
            plan = self.planner.plan(goal)
            if not plan:
                log.append(f"  HIBA: Nincs terv")
                # Próbáljunk új fogalmakat felfedezni a hiányzó szavakból
                self._learn_from_failed_plan(goal)
                continue
            
            log.append(f"  Terv: {', '.join(s.action for s in plan.steps)}")
            
            code = self.generator.generate(plan, language)
            if not code:
                log.append(f"  HIBA: Nincs kód")
                continue
            
            # Validáció
            issues = self._validate_code(code, language)
            
            if not issues:
                log.append(f"  OK: {len(code)} char")
                self.learn_from_success(goal, plan, language)
                return code, log
            
            log.append(f"  Problémák: {len(issues)}")
            for issue in issues:
                log.append(f"    - {issue}")
            
            # Hibából tanulás
            if attempt < max_attempts:
                self._learn_from_error(goal, plan, code, issues, language)
                # Újabb felfedezés a javított tudásból
                new_finds = self.discover_all()
                if new_finds:
                    log.append(f"  Javítás után: {len(new_finds)} új felfedezés")
        
        return None, log
    
    def _validate_code(self, code: str, language: str) -> list[str]:
        """Kód ellenőrzése (nyelvspecifikus)."""
        issues = []
        
        if language == "python":
            try:
                compile(code, '<dka>', 'exec')
            except SyntaxError as e:
                issues.append(f"Szintaxis hiba: {e.msg}")
        elif language == "html":
            code_upper = code.upper()
            if "<!DOCTYPE HTML>" not in code_upper:
                issues.append("Hiányzó DOCTYPE")
            if "<HTML" not in code_upper:
                issues.append("Hiányzó <html>")
        
        return issues
    
    def _learn_from_failed_plan(self, goal: str):
        """Ha nem sikerült terv, keressünk új szavakat."""
        for word in goal.lower().split():
            if len(word) > 3 and word not in self.graph.concepts:
                c = Concept(name=word, description=f"Felismert: '{goal}'",
                          confidence=0.2)
                self.graph.add(c)
                self.discoveries.append(f"[ÚJ FOGALOM] '{word}' a '{goal}' feladatból")
    
    def _learn_from_error(self, goal: str, plan: Plan, code: str,
                          issues: list[str], language: str):
        """Hibából tanulás — hiányzó template-ek, kapcsolatok pótlása."""
        dialect = self.generator.dialects.get(language)
        if not dialect:
            return

        for step in plan.steps:
            # Hiányzó template?
            if not dialect.get_template(step.action):
                # Generáljunk egyet
                fallback = step.action
                if language == "html":
                    fallback = f"<div class=\"{step.action}\">{{children}}</div>"
                elif language == "python":
                    fallback = f"# {step.action}: {{body}}"
                dialect.map(step.action, fallback)
                self.discoveries.append(
                    f"[HIBA→TEMPLATE] {language}: '{step.action}'"
                )

    def execute_and_fix(self, code: str, language: str, mode: str = "python") -> tuple[bool, str]:
        """Kód futtatása és automatikus javítás hiba esetén. Visszaadja (siker, javított_kód)."""
        import subprocess, tempfile, os, re
        max_attempts = 3
        current_code = code
        
        for attempt in range(max_attempts):
            # 1. Mentés temp fájlba
            suffix = ".py" if language == "python" else ".html"
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as f:
                f.write(current_code)
                tmp_path = f.name
            
            try:
                if language == "python":
                    # Python: compile check + runtime check (ha nincs pygame, csak szintaxis)
                    compile(current_code, '<dka_test>', 'exec')
                    
                    # Runtime teszt: import check
                    if 'pygame' in current_code:
                        os.environ['SDL_VIDEODRIVER'] = 'dummy'
                    
                    # Próbáljuk futtatni 3 másodperc timeouttal
                    result = subprocess.run(
                        [_sys.executable, tmp_path],
                        capture_output=True, text=True, timeout=3,
                        env={**os.environ, 'SDL_VIDEODRIVER': 'dummy'}
                    )
                    if result.returncode == 0:
                        # Siker
                        if attempt > 0:
                            self.discoveries.append(f"[AUTO-JAVÍTÁS] {attempt}. próbálkozásra sikerült")
                        return True, current_code
                    else:
                        # Hiba: próbáljuk javítani
                        error_msg = result.stderr[:200]
                        self.discoveries.append(f"[AUTO-JAVÍTÁS] #{attempt+1}: {error_msg[:60]}")
                        current_code = self._fix_code_error(current_code, error_msg, language)
                elif language == "html":
                    # HTML: csak szintaxis ellenőrzés
                    if '<!DOCTYPE' not in current_code.upper():
                        current_code = '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n<title>Oldal</title>\n</head>\n<body>\n' + current_code + '\n</body>\n</html>'
                    return True, current_code
            except SyntaxError as e:
                error_msg = str(e)
                self.discoveries.append(f"[AUTO-JAVÍTÁS] Szintaxis hiba #{attempt+1}")
                current_code = self._fix_code_error(current_code, error_msg, language)
            except subprocess.TimeoutExpired:
                self.discoveries.append("[AUTO-JAVÍTÁS] Időtúllépés — elfogadva")
                return True, current_code  # Timeout = valószínűleg game loop, az OK
            except Exception as e:
                current_code = self._fix_code_error(current_code, str(e), language)
            finally:
                try: os.unlink(tmp_path)
                except: pass
        
        return False, current_code

    def _fix_code_error(self, code: str, error: str, language: str) -> str:
        """Kód automatikus javítása hibaüzenet alapján."""
        # Ismert hibajavítások
        if "import pygame" in error and "No module" in error:
            code = code.replace('import pygame', '# pygame nem elerheto')
            return code
        if "NameError" in error and "not defined" in error:
            # Próbáljuk kitalálni a hiányzó változót
            import re
            var_match = re.search(r"name '(\w+)' is not defined", error)
            if var_match:
                var_name = var_match.group(1)
                # Add default definition
                code = f"{var_name} = None\n" + code
        if "SyntaxError" in error and "invalid syntax" in error:
            # Próbáljuk kijavítani a szintaxis hibát — zárójelek, kettőspontok
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if line.strip().endswith(('try', 'except', 'if', 'elif', 'else', 'for', 'while', 'def', 'class', 'with')):
                    if not line.strip().endswith(':'):
                        lines[i] = line + ':'
                    # Ha nincs body, adjunk hozzá pass-t
                    if i+1 < len(lines) and lines[i+1].strip() and not lines[i+1].startswith((' ', '\t')):
                        lines.insert(i+1, '    pass')
            code = '\n'.join(lines)
        return code

    def run_with_test(self, goal: str, language: str = "python",
                      max_attempts: int = 3) -> tuple[Optional[str], list[str]]:
        """Teljes ciklus: tervez → generál → futtat → javít → újra."""
        log = []
        discoveries = self.discover_all()
        if discoveries:
            log.append(f"Felfedezések a meglévő tudásból:")
            for d in discoveries[:3]:
                log.append(f"  {d}")

        for attempt in range(1, max_attempts + 1):
            log.append(f"[{attempt}/{max_attempts}] {goal}")
            plan = self.planner.plan(goal)
            if not plan:
                log.append(f"  HIBA: Nincs terv")
                self._learn_from_failed_plan(goal)
                continue

            log.append(f"  Terv: {', '.join(s.action for s in plan.steps)}")
            code = self.generator.generate(plan, language)
            if not code:
                log.append(f"  HIBA: Nincs kód")
                continue

            # Validáció
            if isinstance(code, dict):
                # Multi-file: minden fájlt teszteljünk
                all_ok = True
                for fname, fcode in code.items():
                    ok, fixed = self.execute_and_fix(fcode, language)
                    if not ok:
                        all_ok = False
                        log.append(f"  HIBA ({fname}): futási hiba")
                        code[fname] = fixed
                if all_ok:
                    log.append(f"  OK: {len(code)} fájl")
                    self.learn_from_success(goal, plan, language)
                    return code, log
            else:
                ok, fixed_code = self.execute_and_fix(code, language)
                if ok:
                    log.append(f"  OK: {len(fixed_code)} char")
                    self.learn_from_success(goal, plan, language)
                    return fixed_code, log
                log.append(f"  HIBA: futási hiba, javítás próbálva")
                code = fixed_code

            # Hibából tanulás
            if attempt < max_attempts:
                issues = self._validate_code(code if isinstance(code, str) else '', language)
                self._learn_from_error(goal, plan, code if isinstance(code, str) else '', issues, language)
                new_finds = self.discover_all()
                if new_finds:
                    log.append(f"  Javítás után: {len(new_finds)} új felfedezés")

        return None, log
    
    def report(self) -> str:
        """Teljes jelentés."""
        lines = ["=== ÖNFEJLESZTŐ JELENTÉS ==="]
        lines.append(f"Javítások: {self.improvement_count}")
        lines.append(f"Felfedezések: {len(self.discoveries)}")
        
        if self.discoveries:
            lines.append("\nFelfedezések:")
            for d in self.discoveries[-10:]:
                lines.append(f"  {d}")
        
        return "\n".join(lines)
