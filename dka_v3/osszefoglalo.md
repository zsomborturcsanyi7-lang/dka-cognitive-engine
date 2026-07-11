# DKA V3 — Projekt összefoglaló

## Projekt helye

```
C:\Users\iga\Desktop\DTK model\dka_v3\
```

---

## DKA Game Engine (~1700 sor)

**Fájl:** `llm_game_engine.py`

Teljes játékmotor, ami az LLM által generált 4-7 Python függvényből összerak egy működő 2D játékot. Az LLM csak a játéklogikát adja meg, a DKA motor biztosítja az infrastruktúrát.

### Hogyan működik

```python
engine = DKAEngine()
engine.run("""
    ===init===
    engine.set_var("score", 0)
    engine.set_var("lives", 3)
    
    ===update===
    # mozgás, AI, fizika, ütközés
    # engine.input, engine.particles, engine.timer, stb.
    
    ===draw===
    # rajzolás engine.screen-re
    # engine.ui, engine.particles, engine.tilemap
    
    ===collision===
    return True  # ha game over
    
    ===menu_draw===    (opcionális)
    ===menu_handle===  (opcionális)
    ===menu_init===    (opcionális)
""")
```

### Alrendszerek

| Rendszer | Elérés | Képességek |
|---|---|---|
| **Állapotgép** | `engine.switch_state("PLAYING")` | MENU, PLAYING, PAUSED, GAME_OVER, WIN, INTRO, LEVEL_SELECT |
| **Kamera** | `engine.camera.follow(x, y)` | Követés, shake, screen-to-world, world-to-screen, viewport |
| **Tilemap** | `engine.tilemap.load(data)` | JSON pálya, rétegek, tile ütközés, láthatóság optimalizálás |
| **UI** | `engine.ui.button()` | Gomb (kattintás), label, progress bar, text input |
| **Részecske** | `engine.particles.emit(x, y, 20, "explosion")` | explosion, spark, trail, smoke, rain, snow |
| **Időzítő** | `engine.timer.set("spawn", 2.0)` | Ismétlődő + egyszeri időzítők |
| **Input** | `engine.input.key_pressed(K_SPACE)` | Billentyű (lenyomva + point), egér (pozíció + gomb) |
| **Hang** | `engine.audio.play_sfx("name")` | SFX, zene, hangerő |
| **Mentés** | `engine.save.save(data, 0)` | Save/load, highscore |
| **Filter** | `engine.filter.flash((255,255,255))` | Flash, fade in, fade out |

### Játékos segéd

```python
engine.set_var("score", 100)       # változó tárolás
engine.get_var("score")            # változó lekérés
engine.inc_var("score", 10)        # növelés
engine.trigger_win()               # győzelem
engine.quit()                      # kilépés
```

---

## Generált játékok

### 2D Shooter

```
generated/engine_shooter/
├── game_code.py      — 597 sor játéklogika
└── run_shooter.py    — indító script
```

**Futtatás:**
```bash
cd "C:\Users\iga\Desktop\DTK model\dka_v3\generated\engine_shooter"
python run_shooter.py
```

**Funkciók:**
- 4 enemy típus (Basic, Fast, Tank, Shooter — utóbbi lövi a játékost)
- 3 power-up (Health, Rapid Fire, Shield)
- Hullám rendszer (egyre nehezebb)
- Combo pontrendszer
- Csillagos háttér animáció
- Robbanás + részecske effektek
- Highscore mentés
- Képernyő shake + villanás
- Részletes menü pulzáló címmel

**Irányítás:**
- `← → ↑ ↓` — mozgás
- `SPACE` — lövés
- `ESC` — pause
- `F1` — debug info
- `F12` — screenshot

### További tesztelt játékok

```
generated/engine_platformer/   — platformer (kamera + tilemap + gravitáció + coin)
generated/engine_shootemup/    — shoot'em up (részecske + timerek + combo)
generated/engine_rpg/          — RPG demo (menü + UI + mentés + állapotgép)
```

---

## Amit a DKA tud

- **LLM + DKA páros:** Az LLM bármilyen játéklogikát kitalálhat, a DKA biztosítja hogy a végeredmény működjön
- **Hibajavítás:** Syntax + runtime hibák automatikus javítása
- **Nem kell tökéletes LLM:** A DKA kijavítja a hibákat
- **Nincs context window limit:** A DKA motor állandó, az LLM csak a logikát adja
- **Minden 2D játék:** Ami elfér a Pygame keretrendszerben

---

## Amit a DKA még NEM tud

**❌ Nincs LLM API kapcsolat élesben** — a motor készen várja, de jelenleg kézzel írom a játéklogikát. Kell egy API kulcs (OpenAI, Anthropic, DeepSeek, OpenRouter), hogy az LLM valóban generálja a játékokat.

**❌ Nincs hangfájl** — az audio rendszer beépített, de nincsenek .wav fájlok.

**❌ Nincs sprite betöltés** — minden geometriai alakzatokkal van rajzolva.

---

## Következő lépések

1. LLM API kulcs beállítása
2. LLM által generált játékok tesztelése
3. Skill mentés (a teljes engine + LLM integráció)
4. Több játéktípus automatikus generálása
