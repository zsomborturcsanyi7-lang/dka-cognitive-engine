# DKA V3 — Concept-Based Cognitive Architecture (concept graph + planner + code generator)

**Status:** ⚠️ Prototype — concept graph + planner + simulator tesztelve, LLM game engine működik, self-improver folyamatban

Fogalmi tudásbázisra épülő kognitív architektúra. Nem token predikció, hanem absztrakt fogalmakkal, tervezéssel és szimulációval dolgozik.

## ⚠️ THIS PROJECT IS UNFINISHED — FEEL FREE TO CONTINUE IT ⚠️

**Ez a projekt NINCS KÉSZEN. Bárki folytathatja, aki akarja!**
Ezt a projektet Zsombi & Hermes Agent (Nous Research) közösen fejlesztette, de egyik projekt sincs 100%-osan befejezve.

---

## dka_v3/ — DKA V3 fő verzió

| Fájl | Sorok | Mit csinál |
|------|-------|-----------|
| `concept_graph.py` | 228 | Fogalmi tudásbázis — absztrakt fogalmak, nyelvfüggetlen |
| `planner.py` | — | Feladat → részcélok → fogalmak kiválasztása |
| `generator.py` | — | Fogalmi terv → konkrét kód |
| `simulator.py` | — | Terv szimuláció fogalmi szinten |
| `self_improver.py` | — | Önjavítás: hibákból tanul |
| `semantic_inference.py` | — | Szemantikus következtető |
| `llm_game_engine.py` | — | LLM-driven 2D játékmotor (Pygame) |

## dka_poc/ + dka_v2_archive/
Korábbi verziók: AST bridge, hypergraph, pattern intel, schema engine, stb.

## Fejlesztő
Zsombi & Hermes Agent (Nous Research)
