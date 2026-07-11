# Determinisztikus Kognitív Architektúra (DKA) PoC

Ez a projekt egy kísérleti mesterséges intelligencia architektúra prototípusa, amely elveti a hagyományos statisztikai alapú (Transformer/LLM) megközelítést.

## Alapelvek
- **Determinizmus:** Nincsenek valószínűségi súlyok, csak fix számlálók és logikai kapcsolatok.
- **Valós idejű tanulás:** Nincs külön tanítási fázis; a rendszer a bemeneti szekvenciákból azonnal építi a gráfot.
- **Hipergráf struktúra:** Az információkat Nódusok és Élek (Pointerek) hálózata tárolja.

## Modulok
1. **Receptor:** Tokenizálja a bemeneti szöveget.
2. **Hypergraph:** Tárolja a nódusokat és a közöttük lévő irányított éleket.
3. **Logic Engine:** Gráfbejáró algoritmus a kódgeneráláshoz és validációhoz.
4. **Optimizer:** Automatikusan parancsikonokat (shortcut) hoz létre a gyakori útvonalakhoz.

## 2. Fázis Fejlesztései: Kontextus és Felejtés
A rendszer továbbfejlesztésre került az alábbi funkciókkal:

1. **Kontextus-függő Élek:** Az élek rögzítik az előző 2-3 lépés (nódus) szekvenciáját. A generáló motor ez alapján dönt a kétértelmű elágazásoknál (pl. ugyanaz a változó más műveletben).
2. **Szelektív Felejtés (Decay):** Az élek erőssége idővel csökken. Ha egy kapcsolatot nem erősítenek meg újabb bemenetek, a rendszer elfelejti (törli az élt).

## Futtatás
```bash
python main.py
```

## Demó tartalom
A `main.py` lefuttatása során a rendszer:
1. Megtanul egy egyszerű programozási szintaxist.
2. Generál egy logikailag helyes kódsort a gráf alapján.
3. Felismeri a szintaktikai hibákat (megszakadt gráf-útvonal).
4. Optimalizálja a belső struktúrát shortcutok segítségével.
