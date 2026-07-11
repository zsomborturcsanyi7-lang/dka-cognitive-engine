"""
DKA V3 — Alapfogalmak
======================
Az alapvető absztrakt fogalmak, amikkel minden programozó dolgozik.
Nyelvfüggetlenek! A "lista" itt nem Python list, hanem elemek sorozata.
"""

from concept_graph import (
    ConceptGraph, Concept, Property, Operation, 
    ConceptRelation, RelationType
)


def seed_basic_concepts(graph: ConceptGraph):
    """Alapfogalmak feltöltése a gráfba."""
    
    # ═══════════════════════════════════════════
    # ADATSTRUKTÚRÁK
    # ═══════════════════════════════════════════
    
    graph.add(Concept(
        name="érték",
        description="Egy darab adat. Lehet szám, szöveg, logikai érték.",
        properties=[
            Property("típus", "szöveg", "Milyen típusú: szám, szöveg, logikai"),
        ],
        operations=[
            Operation("összehasonlítás", "Két érték összehasonlítása", 
                     inputs=["érték", "érték"], outputs=["logikai"]),
            Operation("művelet", "Értéken végzett művelet (+, -, stb.)",
                     inputs=["érték", "érték"], outputs=["érték"]),
        ],
        examples=["5", "alma", "igaz"],
    ))
    
    graph.add(Concept(
        name="gyűjtemény",
        description="Több érték tárolása egyben. Van sorrendje, lehet bejárni.",
        properties=[
            Property("hossz", "szám", "Hány eleme van"),
            Property("sorrend", "logikai", "Van-e értelmes sorrendje"),
        ],
        operations=[
            Operation("bejárás", "Minden elemen végigmenni",
                     inputs=["gyűjtemény"], outputs=["érték"],
                     examples=["for x in lista: ...", "lista.forEach(x => ...)"]),
            Operation("hozzáfér", "Egy elem lekérése index alapján",
                     inputs=["gyűjtemény", "szám"], outputs=["érték"]),
            Operation("hozzáad", "Új elem hozzáadása",
                     inputs=["gyűjtemény", "érték"], outputs=["gyűjtemény"]),
            Operation("hossz", "Elemek számának lekérése",
                     inputs=["gyűjtemény"], outputs=["szám"]),
        ],
        relations=[
            ConceptRelation(RelationType.HAS_PROPERTY, "sorrend"),
        ],
        language_mappings={
            "python": "list",
            "javascript": "Array",
            "html": "collection (ul/ol)",
        },
    ))
    
    graph.add(Concept(
        name="szótár",
        description="Kulcs-érték párok gyűjteménye. Kulcs alapján gyors elérés.",
        properties=[
            Property("kulcs_típus", "szöveg", "Milyen típusúak a kulcsok"),
            Property("érték_típus", "szöveg", "Milyen típusúak az értékek"),
        ],
        operations=[
            Operation("kulcs_alapú_elérés", "Érték lekérése kulcs alapján",
                     inputs=["szótár", "érték"], outputs=["érték"]),
            Operation("kulcsok", "Összes kulcs lekérése",
                     inputs=["szótár"], outputs=["gyűjtemény"]),
            Operation("értékek", "Összes érték lekérése",
                     inputs=["szótár"], outputs=["gyűjtemény"]),
        ],
        language_mappings={
            "python": "dict",
            "javascript": "Object/Map",
            "html": "n.a.",
        },
    ))
    
    graph.add(Concept(
        name="szöveg",
        description="Karakterek sorozata. Szöveges adat.",
        properties=[
            Property("hossz", "szám", "Hány karakterből áll"),
        ],
        operations=[
            Operation("darabol", "Szöveg feldarabolása egy elválasztó mentén",
                     inputs=["szöveg", "szöveg"], outputs=["gyűjtemény"]),
            Operation("összefűz", "Több szöveg összefűzése egybe",
                     inputs=["gyűjtemény"], outputs=["szöveg"]),
            Operation("tartalmaz", "Ellenőrzi, hogy tartalmaz-e egy részt",
                     inputs=["szöveg", "szöveg"], outputs=["logikai"]),
        ],
        language_mappings={
            "python": "str",
            "javascript": "String",
            "html": "Text",
        },
    ))
    
    # ═══════════════════════════════════════════
    # MŰVELETEK
    # ═══════════════════════════════════════════
    
    graph.add(Concept(
        name="szűrés",
        description="Kiválogat egy gyűjteményből bizonyos elemeket egy feltétel alapján.",
        operations=[
            Operation("szűrés", "Elemek kiválogatása feltétel alapján",
                     inputs=["gyűjtemény", "feltétel"], outputs=["gyűjtemény"]),
        ],
        relations=[
            ConceptRelation(RelationType.REQUIRES, "feltétel"),
            ConceptRelation(RelationType.PRODUCES, "gyűjtemény"),
        ],
        language_mappings={
            "python": "filter() / list comprehension",
            "javascript": "Array.filter()",
            "html": "n.a.",
        },
    ))
    
    graph.add(Concept(
        name="rendezés",
        description="Gyűjtemény elemeinek sorba rendezése valamilyen szempont szerint.",
        operations=[
            Operation("rendezés", "Elemek sorba rendezése",
                     inputs=["gyűjtemény", "összehasonlítás"], outputs=["gyűjtemény"]),
        ],
        language_mappings={
            "python": "sorted() / .sort()",
            "javascript": "Array.sort()",
        },
    ))
    
    graph.add(Concept(
        name="transzformáció",
        description="Minden elemen végrehajt egy műveletet, és az eredményekből új gyűjteményt készít.",
        operations=[
            Operation("leképzés", "Minden elem átalakítása",
                     inputs=["gyűjtemény", "művelet"], outputs=["gyűjtemény"]),
        ],
        language_mappings={
            "python": "map() / list comprehension",
            "javascript": "Array.map()",
        },
    ))
    
    graph.add(Concept(
        name="összegzés",
        description="Gyűjtemény elemeinek egyetlen értékké alakítása (pl. összegzés, szorzás).",
        operations=[
            Operation("aggregálás", "Elemek összegzése egy értékké",
                     inputs=["gyűjtemény", "művelet", "kezdőérték"], outputs=["érték"]),
        ],
        examples=["lista összegzése", "szavak összefűzése"],
        language_mappings={
            "python": "sum() / reduce()",
            "javascript": "Array.reduce()",
        },
    ))
    
    # ═══════════════════════════════════════════
    # VEZÉRLÉS
    # ═══════════════════════════════════════════
    
    graph.add(Concept(
        name="ciklus",
        description="Valamit többször végrehajtani. Lehet adatokon végigmenve vagy feltételig.",
        operations=[
            Operation("iteráció", "Bejárás gyűjtemény felett",
                     inputs=["gyűjtemény", "művelet"], outputs=[]),
            Operation("feltételes_ciklus", "Ciklus amíg egy feltétel igaz",
                     inputs=["feltétel", "művelet"], outputs=[]),
        ],
        language_mappings={
            "python": "for / while",
            "javascript": "for / while / forEach",
            "html": "n.a.",
        },
    ))
    
    graph.add(Concept(
        name="feltétel",
        description="Döntés: ha valami igaz, akkor ezt csináld, különben azt.",
        operations=[
            Operation("elágazás", "Két út közül választás feltétel alapján",
                     inputs=["logikai", "művelet", "művelet"], outputs=[]),
        ],
        examples=["ha x > 0: ... különben: ..."],
        language_mappings={
            "python": "if / elif / else",
            "javascript": "if / else if / else",
            "html": "n.a.",
        },
    ))
    
    # ═══════════════════════════════════════════
    # LOGIKAI
    # ═══════════════════════════════════════════
    
    graph.add(Concept(
        name="logikai",
        description="Igaz vagy hamis érték. Döntések alapja.",
        properties=[
            Property("lehetséges_értékek", "gyűjtemény", "igaz, hamis"),
        ],
        operations=[
            Operation("és", "Mindkettő igaz kell legyen",
                     inputs=["logikai", "logikai"], outputs=["logikai"]),
            Operation("vagy", "Legalább az egyik igaz kell legyen",
                     inputs=["logikai", "logikai"], outputs=["logikai"]),
            Operation("tagadás", "Fordítottja",
                     inputs=["logikai"], outputs=["logikai"]),
        ],
        examples=["True/False", "true/false", "igaz/hamis"],
    ))
    
    graph.add(Concept(
        name="összehasonlítás",
        description="Két érték viszonyának vizsgálata.",
        relations=[
            ConceptRelation(RelationType.PRODUCES, "logikai"),
        ],
        examples=["egyenlő", "kisebb", "nagyobb", "tartalmaz"],
    ))
    
    # ═══════════════════════════════════════════
    # HTML SPECIFIKUS
    # ═══════════════════════════════════════════
    
    graph.add(Concept(
        name="weblap",
        description="Egy teljes HTML oldal. Tartalmaz fejlécet, tartalmat, esetleg stílust és viselkedést.",
        properties=[
            Property("felépítés", "szöveg", "HTML struktúra: doctype, html, head, body"),
        ],
        operations=[
            Operation("megjelenítés", "Az oldal megjelenítése böngészőben",
                     outputs=["weblap"]),
        ],
        language_mappings={
            "python": "return html_string",
            "javascript": "document.write()",
            "html": "full HTML document",
        },
    ))
    
    graph.add(Concept(
        name="űrlap",
        description="Beviteli mezőket tartalmazó felület. Adatgyűjtésre szolgál.",
        properties=[
            Property("mezők", "gyűjtemény", "A benne lévő input mezők listája"),
            Property("küldési_mód", "szöveg", "GET vagy POST"),
        ],
        operations=[
            Operation("beküldés", "Az űrlap adatainak elküldése",
                     inputs=["űrlap"], outputs=[]),
        ],
        language_mappings={
            "python": "Flask/WTF form",
            "javascript": "document.forms",
            "html": "<form>...</form>",
        },
    ))
    
    graph.add(Concept(
        name="input_mező",
        description="Egy beviteli mező, ahol a felhasználó adatot adhat meg.",
        properties=[
            Property("típus", "szöveg", "text, number, email, password, stb."),
            Property("címke", "szöveg", "A mező mellett megjelenő szöveg"),
        ],
        language_mappings={
            "html": "<input type='...'>",
            "python": "n.a.",
            "javascript": "document.createElement('input')",
        },
    ))
    
    graph.add(Concept(
        name="gomb",
        description="Kattintható elem. Műveletet indít el.",
        operations=[
            Operation("kattintás", "Művelet végrehajtása kattintáskor",
                     inputs=["gomb", "művelet"], outputs=[]),
        ],
        language_mappings={
            "html": "<button>...</button>",
            "javascript": "element.onclick = ...",
        },
    ))
    
    graph.add(Concept(
        name="cím",
        description="Fejléc vagy cím a weboldalon. Általában a legfontosabb szöveg.",
        properties=[
            Property("szint", "szám", "1-6, a fejléc fontossági szintje"),
        ],
        language_mappings={
            "html": "<h1>...</h1>",
        },
    ))
    
    graph.add(Concept(
        name="bekezdés",
        description="Szöveges bekezdés. Folyó szöveg egysége.",
        language_mappings={
            "html": "<p>...</p>",
        },
    ))
    
    # ═══════════════════════════════════════════════
    # ÚJ FOGALMAK (a 300 feladatos teszthez)
    # ═══════════════════════════════════════════════
    
    graph.add(Concept(
        name="minimum",
        description="A legkisebb érték keresése egy gyűjteményben.",
        operations=[
            Operation("minimum", "Legkisebb elem megtalálása",
                     inputs=["gyűjtemény"], outputs=["érték"]),
        ],
        language_mappings={
            "python": "min()",
        },
    ))
    
    graph.add(Concept(
        name="maximum",
        description="A legnagyobb érték keresése egy gyűjteményben.",
        operations=[
            Operation("maximum", "Legnagyobb elem megtalálása",
                     inputs=["gyűjtemény"], outputs=["érték"]),
        ],
        language_mappings={
            "python": "max()",
        },
    ))
    
    graph.add(Concept(
        name="átlag",
        description="Számok átlagának számítása.",
        language_mappings={
            "python": "sum/len",
        },
    ))
    
    graph.add(Concept(
        name="megszámlálás",
        description="Elemek számának megszámolása egy feltétel alapján.",
        operations=[
            Operation("megszámlálás", "Feltételnek megfelelő elemek száma",
                     inputs=["gyűjtemény", "feltétel"], outputs=["szám"]),
        ],
    ))
    
    graph.add(Concept(
        name="fordítás",
        description="Gyűjtemény vagy szöveg megfordítása.",
        operations=[
            Operation("fordítás", "Elemek sorrendjének megfordítása",
                     inputs=["gyűjtemény"], outputs=["gyűjtemény"]),
        ],
        language_mappings={
            "python": "reversed()",
            "javascript": ".reverse()",
        },
    ))
    
    graph.add(Concept(
        name="első",
        description="Az első N elem kiválasztása egy gyűjteményből.",
        operations=[
            Operation("első_n", "Első N elem",
                     inputs=["gyűjtemény", "szám"], outputs=["gyűjtemény"]),
        ],
        language_mappings={
            "python": "[:n]",
        },
    ))
    
    graph.add(Concept(
        name="fájl",
        description="Fájl a fájlrendszerben. Lehet olvasni, írni.",
        operations=[
            Operation("fájl_olvasás", "Fájl tartalmának beolvasása",
                     inputs=["fájl"], outputs=["szöveg"]),
            Operation("fájl_írás", "Szöveg írása fájlba",
                     inputs=["fájl", "szöveg"], outputs=[]),
        ],
        language_mappings={
            "python": "open()",
        },
    ))
    
    graph.add(Concept(
        name="kép",
        description="Kép megjelenítése weboldalon.",
        language_mappings={
            "html": "<img src='...'>",
        },
    ))
    
    graph.add(Concept(
        name="táblázat",
        description="Táblázatos adatmegjelenítés. Sorokból és oszlopokból áll.",
        properties=[
            Property("sorok", "szám", "Hány sora van"),
            Property("oszlopok", "szám", "Hány oszlopa van"),
        ],
        language_mappings={
            "html": "<table>...</table>",
        },
    ))
    
    graph.add(Concept(
        name="link",
        description="Kattintható hivatkozás másik oldalra.",
        language_mappings={
            "html": "<a href='...'>...</a>",
        },
    ))
    
    graph.add(Concept(
        name="stílus",
        description="Megjelenési szabályok. Színek, méretek, elrendezés.",
        language_mappings={
            "html": "<style>...</style>",
            "css": "CSS rules",
        },
    ))
    
    graph.add(Concept(
        name="menü",
        description="Navigációs menü weboldalon.",
        language_mappings={
            "html": "<nav>...</nav>",
        },
    ))
    
    graph.add(Concept(
        name="fejléc",
        description="Weboldal tetején lévő rész. Általában címet és navigációt tartalmaz.",
        language_mappings={
            "html": "<header>...</header>",
        },
    ))
    
    graph.add(Concept(
        name="lábléc",
        description="Weboldal alján lévő rész. Általában copyright és linkek.",
        language_mappings={
            "html": "<footer>...</footer>",
        },
    ))
    
    # ═══════════════════════════════════════════
    # KAPCSOLATOK
    # KAPCSOLATOK
    
    graph.relate("lista", "gyűjtemény", RelationType.IS_A)
    graph.relate("tömb", "gyűjtemény", RelationType.IS_A)
    
    graph.relate("szűrés", "gyűjtemény", RelationType.HAS_OPERATION)
    graph.relate("rendezés", "gyűjtemény", RelationType.HAS_OPERATION)
    graph.relate("transzformáció", "gyűjtemény", RelationType.HAS_OPERATION)
    graph.relate("összegzés", "gyűjtemény", RelationType.HAS_OPERATION)
    graph.relate("bejárás", "gyűjtemény", RelationType.HAS_OPERATION)
    graph.relate("hozzáfér", "gyűjtemény", RelationType.HAS_OPERATION)
    
    graph.relate("páros", "szám", RelationType.HAS_PROPERTY)
    graph.relate("páratlan", "szám", RelationType.HAS_PROPERTY)
    graph.relate("páros", "páratlan", RelationType.OPPOSITE)
    
    graph.relate("űrlap", "weblap", RelationType.PART_OF)
    graph.relate("input_mező", "űrlap", RelationType.PART_OF)
    graph.relate("gomb", "űrlap", RelationType.PART_OF)
    graph.relate("cím", "weblap", RelationType.PART_OF)
    graph.relate("bekezdés", "weblap", RelationType.PART_OF)
    graph.relate("kép", "weblap", RelationType.PART_OF)
    graph.relate("táblázat", "weblap", RelationType.PART_OF)
    graph.relate("link", "weblap", RelationType.PART_OF)
    graph.relate("menü", "weblap", RelationType.PART_OF)
    graph.relate("fejléc", "weblap", RelationType.PART_OF)
    graph.relate("lábléc", "weblap", RelationType.PART_OF)
    graph.relate("stílus", "weblap", RelationType.PART_OF)
    
    graph.relate("szűrés", "feltétel", RelationType.REQUIRES)
    
    graph.relate("lista", "tömb", RelationType.SAME_AS, strength=0.9)
    
    # Új műveleti kapcsolatok
    graph.relate("minimum", "gyűjtemény", RelationType.HAS_OPERATION)
    graph.relate("maximum", "gyűjtemény", RelationType.HAS_OPERATION)
    graph.relate("fordítás", "gyűjtemény", RelationType.HAS_OPERATION)
    graph.relate("átlag", "gyűjtemény", RelationType.HAS_OPERATION)
    graph.relate("megszámlálás", "gyűjtemény", RelationType.HAS_OPERATION)
    
    print(f"  Alapfogalmak betöltve: {graph.stats()['concepts']} koncepció, "
          f"{graph.stats()['relations']} kapcsolat, "
          f"{graph.stats()['operations']} művelet")
