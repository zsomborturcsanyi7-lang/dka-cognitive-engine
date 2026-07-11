# DKA V3 — Új AI Faj
# =====================
# Nem token predikció. Nem mintaillesztés. Nem statisztika.
# Fogalmi megértés + tervezés + szimuláció + önjavítás.

## Alapelvek

1. **Fogalmi réteg (Concept Graph)**
   - Minden "tudás" egy fogalom: definíció + műveletek + kapcsolatok + példák
   - "lista" = elemek sorozata, nem egy Python lista
   - "páros" = osztható 2-vel, nem egy függvény
   - Nyelvfüggetlen: Python/HTML/JS ugyanaz a fogalmi szint

2. **Tervező (Planner)**
   - Feladat → részcélok → minden részcélhoz a megfelelő fogalom
   - "csinálj egy HTML formot" = űrlap fogalom + input mező fogalom + beküldés fogalom
   - Nem keres mintát, hanem összerakja a fogalmakat

3. **Szimulátor (Simulator)**
   - Lefuttatja a tervet a fejében, mielőtt kiadná
   - "van benne form? van benne két input? megfelel a célnak?"
   - Ha nem, visszalép és másik utat próbál

4. **Önjavító (Self-Improver)**
   - "a kimenet rossz, miért?"
   - Hiányzó fogalom → felveszi
   - Rossz kapcsolat → javítja

## Tanulságok V2-ből (amit NEM szabad)

❌ Python AST-ra építeni — nyelvfüggő, bezár
❌ PatternNode kézzel építeni — hibalehetőség
❌ Több száz függvényt betanítani — skálázhatatlan
❌ Mintaillesztéssel "gondolkodást" szimulálni — nem vezet sehova

## Építési sorrend

1. ConceptGraph — a fogalmi tudásbázis
2. Planner — feladat → részcélok → fogalmak
3. Generator — fogalmak → kód (bármilyen nyelven)
4. Simulator — terv ellenőrzése a fejben
5. SelfImprover — hibákból tanulás
