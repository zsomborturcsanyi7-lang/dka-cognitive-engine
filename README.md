# DKA V3 — Concept-Based Cognitive Architecture (concept graph + planner + code generator)

**Status:** ⚠️ Prototype — concept graph + planner + simulator tested, LLM game engine working, self-improver in progress

Concept-based cognitive architecture built on abstract concepts, planning and simulation — not token prediction.

## ⚠️ THIS PROJECT IS UNFINISHED — FEEL FREE TO CONTINUE IT ⚠️

This project was developed by Zsombi & Hermes Agent (Nous Research).

---

## dka_v3/ — DKA V3 main version

| File | Lines | What it does |
|------|-------|-------------|
| `concept_graph.py` | 228 | Concept knowledge base — language-independent abstract concepts |
| `planner.py` | — | Task → subgoals → concept selection |
| `generator.py` | — | Concept plan → concrete code |
| `simulator.py` | — | Plan simulation at concept level |
| `self_improver.py` | — | Self-improvement: learns from mistakes |
| `semantic_inference.py` | — | Semantic inference layer |
| `llm_game_engine.py` | — | LLM-driven 2D game engine (Pygame) |

## dka_poc/ + dka_v2_archive/
Earlier versions: AST bridge, hypergraph, pattern intel, schema engine, etc.

## Developer
Zsombi & Hermes Agent (Nous Research)
