"""
DKA V3 — Teljes LLM integráció
=================================
Használat:
  python generate_with_llm.py "készíts egy sötét fantasy játékot"

A script:
  1. Felépíti a prompt-ot a feladatból
  2. Meghív egy LLM API-t (OpenAI kompatibilis)
  3. Feldolgozza a JSON tervet
  4. DKA legenerálja a kódot
  5. Kimenet: /generated/<fájlok>

Beállítás (környezeti változók):
  LLM_API_KEY=sk-...      (kötelező)
  LLM_MODEL=gpt-4o-mini    (opcionális, alapértelmezett: gpt-4o-mini)
  LLM_ENDPOINT=...         (opcionális, alapértelmezett: https://api.openai.com/v1/chat/completions)
"""

import sys, os, json, subprocess, tempfile, re

# DKA import
sys.path.insert(0, os.path.dirname(__file__) or '.')
from concept_graph import ConceptGraph, Concept, RelationType
from seed_concepts import seed_basic_concepts
from seed_massive import seed_massive
from seed_jatek import seed_jatek
from generator import Generator
from planner import Planner, GoalParser
from llm_bridge import LLMBridge


def call_llm(prompt: str, api_key: str = "", model: str = "",
             endpoint: str = "") -> str:
    """Meghív egy OpenAI-kompatibilis LLM API-t."""
    api_key = api_key or os.environ.get("LLM_API_KEY", "")
    model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
    endpoint = endpoint or os.environ.get("LLM_ENDPOINT",
                                          "https://api.openai.com/v1/chat/completions")
    
    if not api_key:
        return json.dumps({
            "error": "Nincs LLM_API_KEY beállítva",
            "fallback": True,
            "type": "játék",
            "components": ["karakter", "ellenség"],
            "title": "Játék",
            "description": "Alapértelmezett játék",
            "params": {"player_speed": 5, "player_size": 50, "spawn_rate": 0.02,
                       "color_scheme": 0}
        })
    
    try:
        import urllib.request
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000,
        }).encode()
        
        req = urllib.request.Request(
            endpoint, data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return json.dumps({"error": str(e), "fallback": True,
                          "type": "játék", "components": ["karakter", "ellenség"],
                          "title": "Játék", "description": "Alapértelmezett",
                          "params": {"player_speed": 5}})


def extract_json(text: str) -> dict:
    """LLM válaszból kinyeri a JSON-t (ha ```json blokkban van)."""
    # JSON blokk keresése
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        text = match.group(1)
    
    # JSON objektum keresése
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Ha semmi nem működik, alapértelmezett
    return {"type": "játék", "components": ["karakter", "ellenség"],
            "title": "Játék", "description": text[:50],
            "params": {"player_speed": 5, "player_size": 50}}


def main():
    if len(sys.argv) < 2:
        print("Használat: python generate_with_llm.py <feladat leírása>")
        print("Példa: python generate_with_llm.py 'készíts egy sötét fantasy játékot'")
        sys.exit(1)
    
    goal = " ".join(sys.argv[1:])
    print(f"[DKA+LLM] Feladat: {goal}")
    
    # 1. DKA inicializálás
    g = ConceptGraph()
    seed_basic_concepts(g)
    seed_massive(g)
    seed_jatek(g)
    
    parser = GoalParser(g)
    gen = Generator(g)
    planner = Planner(g, parser)
    bridge = LLMBridge(g, parser, gen, planner)
    
    # 2. Prompt építés
    available = ["játék", "weblap", "függvény", "osztály", "algoritmus"]
    prompt = bridge.format_llm_prompt(goal, available)
    print(f"[DKA+LLM] Prompt elküldve az LLM-nek...")
    
    # 3. LLM hívás
    response = call_llm(prompt)
    llm_plan = extract_json(response)
    
    if llm_plan.get("fallback"):
        print(f"[DKA+LLM] ⚠️  LLM nem elérhető, alapértelmezett paraméterekkel")
    else:
        print(f"[DKA+LLM] ✅ LLM válasz: {llm_plan.get('title', '?')}")
        print(f"           Típus: {llm_plan.get('type', '?')}")
        print(f"           Komponensek: {llm_plan.get('components', [])}")
    
    # 4. DKA generálás
    result = bridge.generate_from_llm(llm_plan)
    
    if not result:
        print("[DKA+LLM] ❌ A DKA nem tudott kódot generálni")
        sys.exit(1)
    
    # 5. Kimenet
    out_dir = os.path.join(os.path.dirname(__file__), "generated")
    
    if isinstance(result, dict):
        print(f"[DKA+LLM] ✅ {len(result)} fájl generálva:")
        for fname, code in result.items():
            path = os.path.join(out_dir, fname)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(code)
            print(f"           📄 {fname}: {len(code.split(chr(10)))} sor / {len(code)} char")
    elif isinstance(result, str):
        safe_title = re.sub(r'[^\w]', '_', llm_plan.get('title', 'output').lower())
        fname = f"llm_{safe_title}.py"
        path = os.path.join(out_dir, fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"[DKA+LLM] ✅ 1 fájl: 📄 {fname}: {len(result.split(chr(10)))} sor / {len(result)} char")
    
    print(f"[DKA+LLM] ✅ Kész!")


if __name__ == "__main__":
    main()
