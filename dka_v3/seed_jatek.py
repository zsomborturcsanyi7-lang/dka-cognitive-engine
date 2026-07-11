"""
DKA V3 — Játék koncepciók
==========================
Fogalmak és kapcsolatok a játék generáláshoz.
Pygame alapú akció játék.
"""

from concept_graph import ConceptGraph, Concept, Operation, Property, RelationType


def seed_jatek(graph: ConceptGraph):
    """Játék koncepciók hozzáadása a gráfhoz."""
    count_before = len(graph.concepts)

    # ===== ALAP JÁTÉK FOGALMAK =====
    game_concepts = [
        ("játék", "Teljes játék alkalmazás. Pygame alapú."),
        ("akció_játék", "Akció játék, ahol a játékos mozog és ellenségekkel harcol."),
        ("platform_játék", "Platform játék ugrálással és platformokkal."),
        ("ügyességi_játék", "Ügyességi játék, reakcióidőt igényel."),
        ("játékmenet", "A játék fő ciklusa. Események, frissítés, rajzolás."),
        ("karakter", "Játékos karakter. Mozog, ugrik, interaktál."),
        ("játékos", "A játékos által irányított entitás."),
        ("ellenség", "Ellenséges entitás. Mozog, támad, spawnol."),
        ("lövedék", "Lövedék, amit a karakter vagy ellenség lő."),
        ("platform", "Platform amire a játékos léphet."),
        ("akadály", "Akadály a játékban, ütközni lehet vele."),
        ("pontszám", "Játékos pontszáma."),
        ("élet", "Játékos életek száma."),
        ("szint", "Játék szint/szintszám."),
        ("hátér", "Játék háttér és vizuális elemek."),
        ("menü", "Játék menü rendszer."),
        ("játék_vége", "Játék vége állapot."),
        ("ütközés", "Ütközés detektálás két objektum között."),
        ("spawn", "Entitások létrehozása a játékban."),
        ("sebesség", "Objektum mozgási sebessége."),
        ("gravitáció", "Gravitáció a játékban."),
        ("billentyű", "Billentyűzet események kezelése."),
        ("egér", "Egér események kezelése."),
        ("időzítő", "Játék időzítő és késleltetés."),
        ("képernyő", "Játék ablak és képernyő."),
        ("rajzolás", "Objektumok kirajzolása a képernyőre."),
        ("frissítés", "Objektumok állapotának frissítése."),
        ("esemény", "Játék események (billentyű, egér, ablak)."),
        ("AI", "Mesterséges intelligencia az ellenségekhez."),
        ("háttér_szín", "Háttér színe a játékban."),
        ("szín", "RGB szín definíció."),
    ]

    for name, desc in game_concepts:
        if name not in graph.concepts:
            graph.add(Concept(name=name, description=desc))

    # ===== OPERÁCIÓK =====
    game_ops = [
        ("játék_indítás", "Játék inicializálása és indítása."),
        ("játék_ciklus", "Fő játékciklus: while fut: események + frissítés + rajzolás."),
        ("karakter_mozgás", "Karakter mozgatása billentyűkkel."),
        ("karakter_rajzolás", "Karakter kirajzolása a képernyőre."),
        ("ellenség_spawn", "Új ellenség létrehozása."),
        ("ellenség_mozgás", "Ellenség mozgatása és AI."),
        ("ütközés_vizsgálat", "Ütközés ellenőrzése két objektum között."),
        ("pontszám_frissítés", "Pontszám növelése és kijelzése."),
        ("játék_vége_kezelés", "Játék vége állapot kezelése."),
        ("képernyő_frissítés", "Képernyő tartalmának frissítése."),
        ("esemény_kezelés", "Játék események feldolgozása."),
    ]

    for name, desc in game_ops:
        if name not in graph.concepts:
            graph.add(Concept(name=name, description=desc,
                            operations=[Operation(name, desc)]))

    # ===== KAPCSOLATOK =====
    # Hierarchia: X PART_OF Y = X része Y-nak
    graph.relate("játékmenet", "játék", RelationType.PART_OF)
    graph.relate("menü", "játék", RelationType.PART_OF)
    graph.relate("pontszám", "játék", RelationType.PART_OF)
    graph.relate("karakter", "játékmenet", RelationType.PART_OF)
    graph.relate("ellenség", "játékmenet", RelationType.PART_OF)
    graph.relate("játékmenet", "ütközés", RelationType.REQUIRES)
    graph.relate("játékmenet", "esemény", RelationType.REQUIRES)
    
    # IS_A
    graph.relate("akció_játék", "játék", RelationType.IS_A)
    graph.relate("platform_játék", "játék", RelationType.IS_A)
    graph.relate("ügyességi_játék", "játék", RelationType.IS_A)
    graph.relate("játékos", "karakter", RelationType.IS_A)
    
    # HAS_OPERATION
    graph.relate("karakter", "karakter_mozgás", RelationType.HAS_OPERATION)
    graph.relate("karakter", "karakter_rajzolás", RelationType.HAS_OPERATION)
    graph.relate("ellenség", "ellenség_spawn", RelationType.HAS_OPERATION)
    graph.relate("ellenség", "ellenség_mozgás", RelationType.HAS_OPERATION)
    graph.relate("ütközés", "ütközés_vizsgálat", RelationType.HAS_OPERATION)
    graph.relate("pontszám", "pontszám_frissítés", RelationType.HAS_OPERATION)
    graph.relate("játék", "játék_indítás", RelationType.HAS_OPERATION)
    graph.relate("játékmenet", "játék_ciklus", RelationType.HAS_OPERATION)
    
    # PRODUCES
    graph.relate("játék", "játék_vége", RelationType.PRODUCES)
    graph.relate("játékmenet", "pontszám", RelationType.PRODUCES)
    
    # REQUIRES
    graph.relate("karakter", "billentyű", RelationType.REQUIRES)
    graph.relate("ellenség", "AI", RelationType.REQUIRES)
    graph.relate("ütközés_vizsgálat", "ütközés", RelationType.REQUIRES)

    # ===== PYTHON IMPORT-OK =====
    for name, imp in [
        ("játék", "import pygame, random, sys"),
        ("karakter", "import pygame"),
        ("ellenség", "import pygame, random"),
    ]:
        c = graph.get(name)
        if c:
            c.language_mappings["python_import"] = imp

    added = len(graph.concepts) - count_before
    print(f"  [+] {added} játék fogalom (osszesen: {len(graph.concepts)})")
    return graph
