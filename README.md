# DKA V3 — Concept-Based Cognitive Architecture

**Status:** ⚠️ Prototype — concept graph + planner + simulator tested, LLM game engine working, self-improver in progress

**Concrete:** Fogalmi tudásbázisra épülő kognitív architektúra, ami nem token predikcióval dolgozik, hanem absztrakt fogalmakkal, tervezéssel és szimulációval.

## ⚠️ THIS PROJECT IS UNFINISHED — FEEL FREE TO CONTINUE IT ⚠️

**Ez a projekt NINCS KÉSZEN. Bárki folytathatja, aki akarja!**
Ezt a projektet Zsombi & Hermes Agent (Nous Research) közösen fejlesztette, de egyik projekt sincs 100%-osan befejezve. Ha tetszik az ötlet és tovább fejlesztenéd, nyugodtan fork-old, folytasd, és csinálj belőle valami nagyszerűt!

---

## Mi van a repóban

### dka_v3/ — DKA V3 fő verzió

| Fájl | Sorok | Mit csinál |
|------|-------|-----------|
| `concept_graph.py` | 228 | Fogalmi tudásbázis — absztrakt fogalmak (definíció + műveletek + kapcsolatok), nyelvfüggetlen |
| `planner.py` | — | Feladat → részcélok → megfelelő fogalmak kiválasztása |
| `generator.py` | — | Fogalmi terv → konkrét kód (bármilyen nyelven) |
| `simulator.py` | — | Terv szimuláció fogalmi szinten (kód futtatása nélkül) |
| `self_improver.py` | — | Önjavítás: hibákból tanul, hiányzó fogalmakat felvesz |
| `self_improver_v2.py` | — | Javított önjavító verzió |
| `semantic_inference.py` | — | Szemantikus következtető réteg |
| `knowledge_query.py` | — | Tudásbázis lekérdező |
| `llm_game_engine.py` | — | LLM-driven 2D játékmotor (Pygame). LLM adja a logikát (init/update/draw), DKA az infrastruktúrát |
| `learning_test.py` | — | Tanulási teszt |
| `test_engine.py` | — | Engine tesztek |
| `test_300.py` | — | 300 tesztes validáció |
| `template_optimizer.py` | — | Sablon optimalizáló |
| `seed_concepts.py` | — | Seed fogalmak |
| `seed_massive.py` | — | Nagy seed adatbázis |
| `seed_jatek.py` | — | Játék seed adatok |

### dka_poc/ — DKA Proof of Concept (eredeti kísérlet)
AST bridge, receptor, hypergraph, batch training, inference engine, optimization, encryption, snake game logic, vault system, stb.

### dka_v2_archive/ — DKA V2 (archivált)
Hypergraph V2, pattern intel, schema engine, semantic layer, synthesis engine, mass training, stb.

## Hogy működik (V3)

1. **ConceptGraph** — minden "tudás" egy fogalom: definíció + műveletek + kapcsolatok + példák
   - "lista" = elemek sorozata (nem Python lista)
   - "páros" = osztható 2-vel (nem egy függvény)
   - Nyelvfüggetlen: ugyanaz a fogalom → Python/HTML/JS

2. **Planner** — feladat → részcélok → minden részcélhoz a megfelelő fogalom
   - "csinálj egy HTML formot" = űrlap fogalom + input mező + beküldés
   - Nem keres mintát, hanem összerakja a fogalmakat

3. **Simulator** — lefuttatja a tervet "fejben", mielőtt kódot gyártana
   - "van benne form? van két input? megfelel a célnak?"
   - Ha nem, visszalép és másik utat próbál

4. **Self-Improver** — "a kimenet rossz, miért?"
   - Hiányzó fogalom → felveszi
   - Rossz kapcsolat → javítja

## Amit NEM csinál
- Nem token predikció
- Nem mintaillesztés
- Nem statisztikai nyelvmodellezés

## Fejlesztő
Zsombi & Hermes Agent (Nous Research)
