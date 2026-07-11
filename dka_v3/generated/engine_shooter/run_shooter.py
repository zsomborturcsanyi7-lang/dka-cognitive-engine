#!/usr/bin/env python3
"""
DKA V3 — 2D Shooter indító
===========================
Futtatás: python run_shooter.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_game_engine import DKAEngine

# Játék logika betöltése
game_dir = os.path.dirname(os.path.abspath(__file__))
code_path = os.path.join(game_dir, "game_code.py")

with open(code_path, 'r', encoding='utf-8') as f:
    content = f.read()

# A SHOOTER_CODE változó kinyerése
exec_globals = {}
exec(content, exec_globals)
shooter_code = exec_globals.get("SHOOTER_CODE", "")

if not shooter_code:
    print("❌ HIBA: nincs SHOOTER_CODE a game_code.py-ben")
    sys.exit(1)

# Engine indítás
engine = DKAEngine(
    width=800,
    height=600,
    fps=60,
    title="2D Shooter — DKA V3 + LLM",
    game_dir=game_dir,
)

print("🎮 2D Shooter indítása...")
print("   Nyilak: mozgas | SPACE: loves | ESC: pause")
print("   F1: debug | F12: screenshot")
engine.run(shooter_code)
