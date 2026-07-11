# GEMINI.md - DKA Project Instructional Context

## Project Overview
**Deterministic Cognitive Architecture (DKA) PoC** is an experimental AI architecture that rejects statistical weights and probabilistic predictions (e.g., Transformers/LLMs) in favor of a strictly deterministic, graph-based logic system. It learns symbolic relationships and temporal sequences in real-time using a counter-based directed hypergraph.

### Key Modules
- **Receptor (`receptor.py`):** A syntax-aware tokenizer that atomizes input text (source code, config) into discrete symbolic IDs.
- **Hypergraph (`hypergraph.py`):** The central knowledge base. Stores `Node` and `MetaNode` (abstractions) connected by context-aware `Edge` objects with observation counters.
- **Logic Engine (`engine.py`):** The reasoning core. Performs deterministic pathfinding for code generation and executes `self_check()` diagnostics to detect logical loops or inconsistencies.
- **Optimizer (`optimizer.py`):** Manages graph hygiene via selective forgetting (decay), path compression (shortcuts), and topological signature analysis.
- **Rule Engine (`rules.py`):** Applies formal refactoring rules with a Snapshot/Rollback mechanism to ensure logical integrity.
- **Rule Inductor (`inductor.py`):** Implements basic Inductive Logic Programming (ILP) to autonomously generate optimization rules from repeating patterns.
- **File System Bridge (`bridge.py`, `bridge_cross.py`):** Handles I/O operations and maintains cross-domain consistency (e.g., synchronizing Code and Config changes).
- **Knowledge Base (`knowledge_base.py`, `game_logic.py`):** Stores pre-defined logical primitives and domain-specific blueprints (e.g., Snake game logic).

## Building and Running
The project is written in pure Python and requires no external ML libraries.

### Key Commands
- **Main Demo:** `python main.py` - Runs the current development phase demonstration.
- **Production Readiness Test:** `python production_test.py` - Validates cross-domain integrity (Code/Config/Data).
- **Refactoring Demo:** `python live_demo.py` - Showcases analytical refactoring and safety rollbacks.
- **Batch Training:** `python -u main.py` (Phase 12) - Ingests large-scale datasets into the hypergraph.

### State Persistence
The system's knowledge state is stored in `dka_graph.json` and can be reloaded using `Hypergraph.from_json()`.

## Development Conventions
- **Deterministic Mandate:** NEVER use probabilistic or statistical weights. Logic must be derived from physical graph connections and counters.
- **No External ML:** Strictly forbidden to use PyTorch, TensorFlow, SciKit-Learn, or similar libraries.
- **Hierarchical Abstraction:** Prefer creating `MetaNodes` for frequent sequences to improve reasoning efficiency.
- **Safety First:** All graph modifications via the Rule Engine must be followed by a `self_check()`. If errors are found, a rollback to the last JSON snapshot is mandatory.
- **Context Awareness:** Edges should ideally record a sliding window of preceding nodes (typically 2-3) to disambiguate logical paths.

## TODO / Roadmap
- [ ] Implement a formal Lexer in `receptor.py` to replace regex-based tokenization.
- [ ] Add a comprehensive unit testing suite for core graph operations.
- [ ] Extend `RippleEffectEngine` for more complex cross-domain dependency trees.
