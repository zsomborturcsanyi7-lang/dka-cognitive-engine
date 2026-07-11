"""
DKA V3 — SemanticInferenceLayer (V2)
======================================
A nyelvi ėrtelmező réteg. Képes ismeretlen szavak jelentését
kikövetkeztetni a kontextusból, és azokat TELJESEN integrálni
a pipeline-ba: fogalom létrehozás + parser pattern + generator template.

Példa:
  "három kaszt kártya (harcos, varázsló, íjász)"
  1. Felismeri: "harcos", "varázsló", "íjász" a "kaszt" példányai
  2. "kaszt" hasonlít a "kártya"-hoz
  3. Létrehoz: 3 fogalmat IS_A "kártya"
  4. Regisztrál: parser pattern "harcos" -> ("kártya", "weblap")
  5. Template-t ad: "harcos" -> card template specifikus névvel
  6. post_process_plan: hozzáad gyerek lépéseket a kártyákhoz
"""

from __future__ import annotations
import re
from concept_graph import ConceptGraph, Concept, RelationType
from planner import GoalParser, PlanStep, Plan
from generator import Generator


class SemanticInferenceLayer:
    """
    Nyelvi értelmező réteg V2.
    Képes ismeretlen szavak jelentését kikövetkeztetni a kontextusból,
    és TELJESEN INTEGRÁLNI a teljes pipeline-ba.
    """

    def __init__(self, graph: ConceptGraph, parser: GoalParser, generator: Generator = None):
        self.graph = graph
        self.parser = parser
        self.generator = generator
        self.inferred_count = 0
        # Nyilvántartjuk a most inferált fogalmakat (név -> kategória)
        self._recent_inferences: dict[str, str] = {}

    # ══════════════════════════════════════════════
    # NYELVI GAZDAGÍTÁS
    # ══════════════════════════════════════════════

    def enrich_goal(self, goal: str) -> str:
        """Cél szöveg gazdagítása inferált fogalmakkal."""
        enriched = goal
        self._recent_inferences = {}

        # 1. Zárójeles felsorolások
        enriched = self._parse_parenthesized_list(enriched)

        # 2. Ismeretlen szavak
        enriched = self._infer_unknown_words(enriched)

        # 3. Számosság + felsorolás összekapcsolása
        enriched = self._link_quantity_to_list(enriched)

        # 4. Relációs kifejezések: "aki", "amely", "ahol"
        enriched = self._parse_relational_expressions(enriched)

        # 5. Többszavas fogalmak detektálása
        enriched = self._detect_multiword_concepts(enriched)

        return enriched

    # ══════════════════════════════════════════════
    # 1. ZÁRÓJELES FELSOROLÁSOK
    # ══════════════════════════════════════════════

    def _parse_parenthesized_list(self, text: str) -> str:
        """Zárójeles felsorolások felismerése és TELJES INTEGRÁCIÓ."""
        pattern = r'(\w+(?:\s+\w+)?)\s*\(([^)]+)\)'

        def replacer(match):
            category = match.group(1).lower()
            items_text = match.group(2)
            items = [item.strip().lower() for item in items_text.split(',')]

            # Toldalék levágása a kategória szóról
            category_words = category.split()
            last_word = category_words[-1]
            category_stripped = last_word
            for s in ['val','vel','t','ban','ben','ra','re','nak','nek','bol','bel']:
                if last_word.endswith(s) and len(last_word) > len(s) + 3:
                    category_stripped = last_word[:-len(s)]
                    break

            # Kategória felismerése
            category_concept = self._find_closest_concept(last_word)
            if not category_concept:
                category_concept = self._find_closest_concept(category_stripped)
            if not category_concept:
                # Ékezetmentes keresés
                import unicodedata
                def no_acc(s):
                    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
                for cn in self.graph.concepts:
                    if no_acc(cn.lower()) == no_acc(category_stripped):
                        category_concept = cn
                        break

            if category_concept:
                print(f'  [INFER] "{category}" → {category_concept} (kategoria)')
                for item in items:
                    if item not in self.graph.concepts:
                        # 1. Fogalom létrehozása
                        new_concept = Concept(
                            name=item,
                            description=f"{category_concept} példánya",
                            confidence=0.7,
                        )
                        self.graph.add(new_concept)
                        self.graph.relate(item, category_concept,
                                        RelationType.IS_A, strength=0.8)
                        self.inferred_count += 1
                        self._recent_inferences[item] = category_concept

                        # 2. Parser pattern regisztrálás!
                        # "harcos" -> ("kártya", "weblap")
                        self.parser._task_patterns[item] = (category_concept, "")

                        # 3. Generator template regisztrálás!
                        if self.generator:
                            for lang, dialect in self.generator.dialects.items():
                                if lang == "html" and not dialect.get_template(item):
                                    # Kártya template a specifikus névvel
                                    card_tpl = f"""<div class="card" style="background:#f8f9fa;padding:20px;border-radius:8px;margin:15px 0;border-left:4px solid #e74c3c;">
    <h3 style="margin-bottom:10px;color:#2c3e50;">{item.capitalize()}</h3>
    <p>A(z) {item.capitalize()} egy {category_concept} típus, egyedi képességekkel és tulajdonságokkal rendelkezik.</p>
</div>"""
                                    dialect.map(item, card_tpl)
                                elif lang not in ("html",) and not dialect.get_template(item):
                                    dialect.map(item, f"# {item} ({category_concept})")

                        print(f'  [INFER] Új fogalom: "{item}" → {category_concept} (pattern+template)')
                    else:
                        # Már létezik a fogalom, de lehet hogy nincs pattern
                        if item not in self.parser._task_patterns:
                            self.parser._task_patterns[item] = (category_concept, "")
                            self._recent_inferences[item] = category_concept
                        if self.generator and not self.generator.dialects.get("html").get_template(item):
                            dialect = self.generator.dialects.get("html")
                            if dialect:
                                dialect.map(item, f"""<div class="card" style="background:#f8f9fa;padding:20px;border-radius:8px;margin:15px 0;border-left:4px solid #e74c3c;">
    <h3 style="margin-bottom:10px;color:#2c3e50;">{item.capitalize()}</h3>
    <p>A(z) {item.capitalize()} egy specializált {category_concept} komponens.</p>
</div>""")
            else:
                # Ha a kategória ismeretlen, próbáljunk hasonlót
                for known in ['kártya', 'kartya', 'card', 'elem', 'tipus', 'card']:
                    if self._word_similarity(category_stripped, known) > 0.3:
                        category_concept = known
                        print(f'  [INFER] "{category}" → {known} (hasonlóság alapján)')
                        for item in items:
                            if item not in self.graph.concepts:
                                c = Concept(name=item, description=f'{known} példánya', confidence=0.5)
                                self.graph.add(c)
                                self.graph.relate(item, known, RelationType.IS_A, strength=0.5)
                                self.inferred_count += 1
                                self._recent_inferences[item] = known
                                # Pattern + template
                                self.parser._task_patterns[item] = (known, "")
                                if self.generator:
                                    for lang, dialect in self.generator.dialects.items():
                                        if lang == "html" and not dialect.get_template(item):
                                            dialect.map(item, f"""<div class="card" style="background:#f8f9fa;padding:20px;border-radius:8px;margin:15px 0;border-left:4px solid #e74c3c;">
    <h3 style="margin-bottom:10px;color:#2c3e50;">{item.capitalize()}</h3>
    <p>A(z) {item.capitalize()} egy specializált {known} komponens.</p>
</div>""")
                        break

            return f'{category} {items_text}'

        return re.sub(pattern, replacer, text)

    # ══════════════════════════════════════════════
    # 2. ISMERETLEN SZAVAK KÖVETKEZTETÉSE
    # ══════════════════════════════════════════════

    def _infer_unknown_words(self, text: str) -> str:
        """Ismeretlen szavak következtetése a kontextusból."""
        words = text.lower().split()
        result_words = []

        for word in words:
            clean = word.strip('.,;:!?()[]{}"\'').strip("'\"")

            if not clean:
                result_words.append(word)
                continue

            # Már ismert
            if self.parser.is_action_word(clean) or clean in self.graph.concepts:
                result_words.append(word)
                continue

            # Rövid / szám
            if len(clean) < 3:
                result_words.append(word)
                continue
            if clean in ('egy','ket','harom','negy','ot','hat','het','nyolc','kilenc','tiz',
                        'két','három','négy','öt','hét','nyolc','kilenc','tíz'):
                result_words.append(word)
                continue

            # Hasonlóság keresése
            best_match = None
            best_score = 0

            for concept_name in self.graph.concepts:
                if concept_name in ('egy','ket','harom','negy','ot','hat','het','nyolc'):
                    continue
                cn_lower = concept_name.lower()
                clean_lower = clean.lower()
                import unicodedata
                def strip_acc(s):
                    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
                if strip_acc(clean_lower) == strip_acc(cn_lower):
                    best_match = concept_name
                    best_score = 1.0
                    break
                score = self._word_similarity(clean, cn_lower)
                if score > best_score and score > 0.50:
                    best_score = score
                    best_match = concept_name

            if best_match:
                if clean not in self.graph.concepts:
                    c = Concept(name=clean,
                              description=f"Szinonima: {best_match} (következtetés)",
                              confidence=0.5)
                    self.graph.add(c)
                    self.graph.relate(clean, best_match,
                                    RelationType.SAME_AS, strength=0.6)
                    self.inferred_count += 1

                # Parser pattern hozzáadása ha action
                if not self.parser.is_action_word(clean):
                    action_of = self.parser._task_patterns.get(best_match)
                    if action_of:
                        self.parser._task_patterns[clean] = action_of

                # Ékezetmentes verzió használata a szövegben (parser felismeri)
                import unicodedata
                def no_acc(s):
                    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
                no_acc_match = no_acc(best_match)
                # Ha az ékezetmentes verzió NEM egyezik a best_match-tel,
                # adjuk hozzá a _task_patterns-hez
                if no_acc_match != best_match and not self.parser.is_action_word(no_acc_match):
                    action_of = self.parser._task_patterns.get(best_match)
                    if action_of:
                        self.parser._task_patterns[no_acc_match] = action_of
                result_words.append(no_acc_match)
                print(f'  [INFER] "{clean}" → {best_match} ({best_score:.0%})')
            else:
                result_words.append(word)

        return ' '.join(result_words)

    # ══════════════════════════════════════════════
    # 3. SZÁMOSSÁG + FELSOROLÁS
    # ══════════════════════════════════════════════

    def _link_quantity_to_list(self, text: str) -> str:
        """Számosság és felsorolás összekapcsolása."""
        numbers = {
            'egy': 1, 'két': 2, 'ket': 2, 'kettő': 2, 'ketto': 2,
            'három': 3, 'harom': 3, 'négy': 4, 'negy': 4,
            'öt': 5, 'ot': 5, 'hat': 6, 'hét': 7, 'het': 7,
            'nyolc': 8, 'kilenc': 9, 'tíz': 10, 'tiz': 10,
        }
        pattern = r'(\w+)\s+(\w+)\s*\(([^)]+)\)'

        def replacer(match):
            num_word = match.group(1).lower()
            category = match.group(2).lower()
            items_text = match.group(3)
            items = [item.strip().lower() for item in items_text.split(',')]
            expected = numbers.get(num_word, 0)
            actual = len(items)
            if expected > 0 and actual > 0 and expected != actual:
                print(f'  [INFER] Számosság javítva: {num_word}={expected} → {actual}')
            if actual >= 2:
                items_str = ' es '.join(items)
                return f'{num_word} {items_str}'
            return match.group(0)

        return re.sub(pattern, replacer, text)

    # ══════════════════════════════════════════════
    # 4. RELÁCIÓS KIFEJEZÉSEK
    # ══════════════════════════════════════════════

    def _parse_relational_expressions(self, text: str) -> str:
        """Relációs kifejezések: "aki", "amely", "ahol" felismerése."""
        import re
        patterns = [
            (r'(egy\s+\w+)\s+aki\s+(\w+)', 2),
            (r'(egy\s+\w+)\s+amely\s+(\w+)', 2),
            (r'(\w+)\s+ahol\s+(\w+)', 2),
        ]
        for pattern, group in patterns:
            match = re.search(pattern, text)
            if match:
                subject = match.group(1)
                action_word = match.group(2)
                print(f'  [INFER REL] \"{subject}\" + \"{action_word}\" → reláció')
        return text

    # ══════════════════════════════════════════════
    # 5. TÖBBSZAVAS FOGALMAK
    # ══════════════════════════════════════════════

    def _detect_multiword_concepts(self, text: str) -> str:
        """Többszavas fogalmak: "sötét erdő", "gyors autó" → összevonás."""
        import unicodedata
        def no_acc(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        words = text.lower().split()
        result = []
        skip_next = False
        known_pairs = {
            'sötét_erdő': 'terület', 'gyors_autó': 'jármű',
            'repülő_ellenség': 'ellenség', 'mozgó_platform': 'platform',
            'élet_pont': 'pontszám', 'játék_vége': 'játék_vége',
            'fő_menu': 'menü', 'háttér_szín': 'szín',
        }
        for i, word in enumerate(words):
            if skip_next:
                skip_next = False
                result.append(word)
                continue
            if i + 1 < len(words):
                pair = word + '_' + words[i + 1]
                if pair in self.graph.concepts or no_acc(pair) in [no_acc(c) for c in self.graph.concepts]:
                    result.append(pair)
                    skip_next = True
                    continue
                if pair in known_pairs:
                    if pair not in self.graph.concepts:
                        c = Concept(name=pair, description=f"{known_pairs[pair]}: {pair}",
                                   confidence=0.6)
                        self.graph.add(c)
                        self.graph.relate(pair, known_pairs[pair], RelationType.IS_A, strength=0.6)
                        self.inferred_count += 1
                        print(f'  [INFER MULTI] \"{pair}\" → {known_pairs[pair]}')
                    result.append(pair)
                    skip_next = True
                    continue
            result.append(word)
        return ' '.join(result)

    # ══════════════════════════════════════════════
    # POST-PROCESS
    # ══════════════════════════════════════════════

    def post_process_plan(self, plan: Plan) -> Plan:
        """Terv utófeldolgozása: inferált fogalmak FELÜLÍRJÁK a generikus lépéseket.

        Pl. van 3 "kártya" lépés és 3 inferált (harcos, varázsló, íjász) IS_A kártya
        → a kártya lépések action-ját felülírjuk a specifikus névvel.
        """
        # Összegyűjtjük a most inferált fogalmakat kategóriánként
        inferred_by_parent = {}
        for inf_name, parent_cat in self._recent_inferences.items():
            if parent_cat not in inferred_by_parent:
                inferred_by_parent[parent_cat] = []
            inferred_by_parent[parent_cat].append(inf_name)

        new_steps = []
        inferred_used = set()

        # 1. Inferált fogalmak felülírása
        for step in plan.steps:
            if step.action in inferred_by_parent:
                available = [name for name in inferred_by_parent[step.action]
                           if name not in inferred_used]
                if available:
                    inf_name = available[0]
                    inferred_used.add(inf_name)
                    print(f'  [POST_PROCESS] "{inf_name}" felülírja a "{step.action}" lépést')
                    step.action = inf_name
                    step.target = inf_name
                    step.description = f"{inf_name} (specifikus)"
            self._post_process_children(step, inferred_by_parent, inferred_used)
            new_steps.append(step)

        # 2. Ha van "weblap" root, a többi weboldalhoz tartozó root-ot
        #    gyűjtsük a weblap {children} részébe (hogy ne a </html> után jöjjenek)
        weblap_step = None
        other_steps = []
        for step in new_steps:
            if step.action in ("weblap", "weboldal", "html", "page"):
                weblap_step = step
            else:
                other_steps.append(step)

        if weblap_step and other_steps:
            # A többi lépés a weblap gyereke lesz (ha van hely)
            # Ellenőrizzük, hogy a weblap template használ-e {children}-t
            # Ha igen, a többi lépést tegyük gyerekek közé
            for ostep in other_steps:
                # Ne tegyük be ha már benne van a gyerekek között
                if not any(c.action == ostep.action for c in weblap_step.children):
                    weblap_step.children.append(ostep)
                    print(f'  [POST_PROCESS] "{ostep.action}" beágyazva "{weblap_step.action}"-ba')

            plan.steps = [weblap_step]  # Csak a weblap marad root
        else:
            plan.steps = new_steps

        return plan

    def _post_process_children(self, step: PlanStep, inferred_by_parent: dict, inferred_used: set):
        """Gyerek lépések utófeldolgozása."""
        new_children = []
        for child in step.children:
            if child.action in inferred_by_parent:
                available = [name for name in inferred_by_parent[child.action]
                           if name not in inferred_used]
                if available:
                    inf_name = available[0]
                    inferred_used.add(inf_name)
                    child.action = inf_name
                    child.target = inf_name
                    child.description = f"{inf_name} ({inf_name} specifikus)"
                    print(f'  [POST_PROCESS] "{inf_name}" felülírja a "{child.action}" gyereket')
            # Rekurzív
            self._post_process_children(child, inferred_by_parent, inferred_used)
            new_children.append(child)
        step.children = new_children

    # ══════════════════════════════════════════════
    # SEGÉDFÜGGVÉNYEK
    # ══════════════════════════════════════════════

    def _find_closest_concept(self, word: str) -> str:
        """Legközelebbi fogalom keresése (threshold: 0.45)."""
        if word in self.graph.concepts:
            return word
        best = None
        best_score = 0
        for cn in self.graph.concepts:
            score = self._word_similarity(word, cn.lower())
            if score > best_score and score > 0.45:  # 0.3 → 0.45 (kevesebb fals pozitív)
                best_score = score
                best = cn
        return best

    def _word_similarity(self, a: str, b: str) -> float:
        """Szóhasonlóság: prefix + karakter + toldalék levágás + ékezetmentes."""
        if a == b:
            return 1.0
        if not a or not b:
            return 0.0

        import unicodedata
        def no_acc(s):
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

        def strip(word):
            for s in ['val','vel','t','ban','ben','ra','re','nak','nek','bol','bel',
                      'nal','nel','tol','tol','ig','ert','hoz','hez','hez','hoz',
                      'sal','sel','al','el','as','es','ok','ek','ak','ek',
                      'kal','kel','ert','ert','kent','kepp']:
                if word.endswith(s) and len(word) > len(s) + 3:
                    return word[:-len(s)]
            return word

        a_clean = no_acc(strip(a.lower()))
        b_clean = no_acc(strip(b.lower()))

        if a_clean == b_clean:
            return 1.0

        # Prefix
        prefix_len = 0
        for i in range(min(len(a_clean), len(b_clean))):
            if a_clean[i] == b_clean[i]:
                prefix_len += 1
            else:
                break
        prefix_score = prefix_len / max(len(a_clean), len(b_clean), 1)
        common = sum(1 for c in a_clean if c in b_clean)
        char_score = common / max(len(a_clean), len(b_clean), 1)

        return max(prefix_score * 0.7 + char_score * 0.3, prefix_score)

    def report(self) -> str:
        """Jelentés az inferált fogalmakról."""
        lines = ["=== NYELVI ÉRTELMEZŐ JELENTÉS ==="]
        lines.append(f"Összes inferált fogalom: {self.inferred_count}")
        if self._recent_inferences:
            lines.append(f"Legutóbbi inferálások:")
            for name, cat in self._recent_inferences.items():
                lines.append(f"  {name} → {cat}")
        return "\n".join(lines)
