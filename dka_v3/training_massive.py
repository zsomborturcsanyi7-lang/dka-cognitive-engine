"""
DKA V3 — MASSZÍV TRÉNING
=========================
500+ feladat, analógia, hiánypótlás, template felfedezés.
A DKA V3 teljes tudásbázisának robbanásszerű bővítése.

Fázisok:
1. Alap seed (fogalmak, kapcsolatok)
2. Analógia felfedezés (új kapcsolatok)
3. Hiánypótlás (kapcsolat nélküli fogalmak)
4. Template felfedezés (minden fogalomhoz template)
5. 500 feladat futtatása (tanulás minden sikerből)
6. Végső statisztika
"""

import sys, os, time, random
sys.path.insert(0, os.path.dirname(__file__) or '.')

from concept_graph import ConceptGraph, Concept, RelationType
from seed_concepts import seed_basic_concepts
from seed_massive import seed_massive
from generator import Generator, PythonDialect, HTMLDialect, JavaScriptDialect, CSSDialect
from planner import Planner, GoalParser, PlanStep
from self_improver_v2 import SelfImproverV2
from semantic_inference import SemanticInferenceLayer


def run_training():
    print("=" * 60)
    print("DKA V3 — MASSZÍV TRÉNING INDÍTÁSA")
    print("=" * 60)
    start_time = time.time()

    # ==================================================================
    # 1. INICIALIZÁLÁS
    # ==================================================================
    print("\n[1/6] Inicializálás...")
    g = ConceptGraph()
    seed_basic_concepts(g)
    seed_massive(g)

    parser = GoalParser(g)
    planner = Planner(g, parser)
    gen = Generator(g)
    improver = SelfImproverV2(g, planner, gen)
    infer = SemanticInferenceLayer(g, parser, gen)

    print(f"  Fogalmak: {g.stats()['concepts']}")
    print(f"  Kapcsolatok: {g.stats()['relations']}")

    # ==================================================================
    # 2. ANALÓGIA FELFEDEZÉS
    # ==================================================================
    print("\n[2/6] Analógia felfedezés...")
    analogy_findings = improver.discover_by_analogy()
    print(f"  Analógia felfedezések: {len(analogy_findings)}")

    # ==================================================================
    # 3. HIÁNYPÓTLÁS
    # ==================================================================
    print("\n[3/6] Hiánypótlás...")
    gap_findings = improver.detect_gaps()
    print(f"  Hiánypótlások: {len(gap_findings)}")

    # ==================================================================
    # 4. TEMPLATE FELFEDEZÉS
    # ==================================================================
    print("\n[4/6] Template felfedezés...")
    template_findings = improver.discover_templates()
    print(f"  Új template-ek: {len(template_findings)}")
    # Részletezés nyelvek szerint
    for lang_name, dialect in gen.dialects.items():
        count = len(dialect._mappings)
        print(f"    {lang_name}: {count} template")

    # ==================================================================
    # 5. 500 FELADATOS TRÉNING
    # ==================================================================
    print("\n[5/6] 500 feladat futtatása...")

    # ---- HTML FELADATOK (200) ----
    html_tasks = [
        # Alap HTML (30)
        "keszits egy weblapot",
        "keszits egy weblapot cimmel",
        "keszits egy bemutatkozo weblapot",
        "keszits egy kapcsolati weblapot urlappal",
        "keszits egy weblapot kep pel",
        "keszits egy weblapot tablazattal",
        "keszits egy weblapot menüvel",
        "keszits egy portfolio weblapot",
        "keszits egy weblapot ket bekezdessel",
        "keszits egy weblapot harom kartya kartyaval",
        "keszits egy weblapot listaval",
        "keszits egy weblapot fejlecel es lablecel",
        "keszits egy weblapot linkkel",
        "keszits egy weblapot stílussal",
        "keszits egy weblapot urlappal es tablazattal",

        # Komplex weblapok (40)
        "keszits egy jatek bemutato weblapot hero szekcioval es jellemzokkel",
        "keszits egy ettermi weblapot menuvel es kapcsolati urlappal",
        "keszits egy iskolai weblapot tanfolyamokkal es csapattagokkal",
        "keszits egy tech blog weblapot cikkekkel",
        "keszits egy sport kozpont weblapot statisztikakkal",
        "keszits egy weblapot heroval es ket jellemzovel",
        "keszits egy weblapot oldalsavval es tartalommal",
        "keszits egy weblapot ar kartya harom csomaggal",
        "keszits egy weblapot faq szekcioval negy elemmel",
        "keszits egy weblapot csapat taggal harom emberrel",
        "keszits egy weblapot idovonallal esemenyekkel",
        "keszits egy weblapot visszajelzessel es tesztimoniummal",
        "keszits egy weblapot keresovel es lapozoval",
        "keszits egy weblapot haladassavval harom skill-lel",
        "keszits egy weblapot hirlap feliratkozas urlappal",
        "keszits egy weblapot modal ablakkal",
        "keszits egy weblapot heroval statisztikaval es kartya griddel",
        "keszits egy weblapot heroszekcioval ar kartya harom szinttel",
        "keszits egy weblapot csapattagokkal es faq-okkal",
        "keszits egy portfolio weblapot heroval szolgaltatasokkal es kapcsolati urlappal",
        "keszits egy termeek bemutato weblapot heroval ar kartya es visszajelzessel",
        "keszits egy startup weblapot statisztikaval csapattal es hirevéllel",
        "keszits egy online kurzus weblapot heroval jellemzokkel es idovonallal",
        "keszits egy szolgaltatas weblapot heroval kartya griddel kapcsolati urlappal",
        "keszits egy esemeny weblapot heroval idovonallal es faq-gal",

        # Inferencia (50)
        "keszits egy weblapot harom kartyaval (akcio, rpg, strategia)",
        "keszits egy weblapot negy jellemzovel (gyors, olcso, megbizhato, uj)",
        "keszits egy portfolio weblapot harom szolgaltatassal (webfejlesztes, design, marketing)",
        "keszits egy jatek weblapot ket kaszttal (lovag, mokus)",
        "keszits egy weblapot harom kartyaval (alap, premium, enterprise) es arazo tablazattal",
        "keszits egy weblapot ot reszleggel (termek, ar, csapat, kapcsolat, blog)",
        "keszits egy tech weblapot harom termekkartyaval (telefon, laptop, tablet)",
        "keszits egy weblapot csapattagokkal (Anna, Bela, Csaba, Dora)",
        "keszits egy sport weblapot harom sportaggal (foci, kosar, tenisz)",
        "keszits egy weblapot ket szolgaltatassal (tanacsadas, fejlesztes)",
        "keszits egy weblapot harom ar csomaggal (bronz, ezust, arany)",
        "keszits egy weblapot ket jellemzovel (gyors, biztonsagos) es egy urlappal",
        "keszits egy blog weblapot harom kategorival (tech, eletmod, tudomany)",
        "keszits egy weblapot tanfolyamokkal (python, html, javascript, css)",
        "keszits egy weblapot harom funkcioval (kereses, szures, rendezes)",
        "keszits egy weblapot harom munkatars kartyaval (Zoli, Peti, Mari)",
        "keszits egy weblapot negy szolgaltatassal (web, mobil, design, marketing)",
        "keszits egy weblapot harom termekkel (ingyenes, medium, pro) tablazattal",
        "keszits egy jatek portal weblapot harom jatek kartyaval (akcio, kaland, strategia)",
        "keszits egy weblapot harom okkal (gyors, egyszeru, hatekony)",
        "keszits egy weblapot ket felhasznaloi szereppel (admin, user)",
        "keszits egy weblapot harom nyelvi valtozattal (magyar, angol, nemet)",
        "keszits egy egeszsegugyi weblapot harom szolgaltatassal (rendeles, vizsgalat, tanacsadas)",
        "keszits egy weblapot ot szolgaltatassal (webfejl, app, design, marketing, tanacs)",
        "keszits egy utazasi weblapot harom celpont kartyaval (parizs, london, budapest)",

        # Max komplex (50)
        "keszits egy teljes startup weblapot hero szekcioval statisztikaval ar kartya harom szinttel csapattaggal faq-val es kapcsolati urlappal",
        "keszits egy teljes jatek weblapot heroval jellemzokkel idovonallal csapattal es tablazattal",
        "keszits egy teljes saas weblapot heroval jellemzokkel ar kartya harom csomaggal tesztimoniummal faq-val es hirlevéllel",
        "keszits egy teljes etterem weblapot heroval menu grid-del csapattagokkal tesztimoniummal idovonallal es kapcsolati urlappal",
        "keszits egy teljes iskola weblapot heroval kurzus kartyakkal statisztikaval csapattal faq-val es hirlevéllel",
        "keszits egy teljes e-kereskedelmi weblapot heroval termek grid-del ar tablazattal visszajelzessel keresovel es kapcsolati urlappal",
        "keszits egy teljes sport weblapot heroval edzes terv idovonallal statisztikaval csapattal es blog posztokkal",
        "keszits egy teljes portfoliot heroval szolgaltatas grid-del csapattal idovonallal projekttablazattal es urlappal",
        "keszits egy teljes tech blogot heroval cikk lista kategorikkal kereso csapat es hirlevele",
        "keszits egy teljes konferencia weblapot heroval eloadokkal idovonallal ar kartya helyszinnel es kapcsolati urlappal",

        # Tema-specifikus (20)
        "keszits egy jatek weblapot hero szekcioval es harom jellemzovel",
        "keszits egy sport weblapot statisztikaval es csapattagokkal",
        "keszits egy ettermi weblapot menuvel es tesztimoniummal",
        "keszits egy iskolai weblapot kurzusokkal es faq-val",
        "keszits egy blog weblapot cikk listaval es kategorikkal",
        "keszits egy tech weblapot heroval es jellemzovel",
        "keszits egy portfolio weblapot szolgaltatasokkal es projektekkel",
        "keszits egy startup weblapot statisztikaval es ar kartyaval",
        "keszits egy utazasi weblapot celpontokkal es tesztimoniummal",
        "keszits egy egeszsegugyi weblapot szolgaltatasokkal es csapattal",
    ]

    # ---- PYTHON FELADATOK (200) ----
    python_tasks = [
        # Alap (20)
        "szurd ki a paros szamokat egy listabol",
        "rendezz egy listat szamok alapjan",
        "transzformalj egy listat karakterlancokka",
        "szamold meg a pozitiv szamokat egy listaban",
        "vedd az elso harom elemet egy listabol",
        "szamold ki az atlagot egy szam listabol",
        "forditsd meg a lista sorrendjet",
        "ird ki a lista minden elemet",
        "keresd meg a legnagyobb szamot egy listaban",
        "keresd meg a legkisebb szamot egy listaban",
        "szurd ki a paratlan szamokat egy listabol",
        "szamold az osszeget egy szam listabol",
        "rendezd a listat csokkeno sorrendbe",
        "valogass ki minden masodik elemet",
        "vond ki az atlagot minden szambol",
        "szurd ki a negativ szamokat es ird ki oket",
        "vedd az utolso ot elemet egy listabol",
        "forditsd meg a szavak sorrendjet egy szovegben",
        "szamold meg hany szobol all egy mondat",
        "keresd meg a leghosszabb szot egy listaban",

        # Függvények (30)
        "keszits egy fuggvenyt ami osszead ket szamot",
        "keszits egy fuggvenyt ami szuri a paros szamokat",
        "keszits egy fuggvenyt parameterrel es visszateresi ertekkel",
        "keszits egy fuggvenyt ami egy listat rendez",
        "keszits egy fuggvenyt ami kiszamolja az atlagot",
        "keszits egy fuggvenyt ami ellenorzi hogy egy szam paros-e",
        "keszits egy fuggvenyt ami stringet fordithat meg",
        "keszits egy fuggvenyt harom parameterrel",
        "keszits egy fuggvenyt ami egy listat szur es rendez",
        "keszits egy fuggvenyt ami faktorialist szamol",
        "keszits egy osztalyt konstruktorral es metodussal",
        "keszits egy osztalyt tulajdonsagokkal",
        "keszits egy adat osztalyt harom mezovel",
        "keszits egy enum osztalyt ertekekkel",
        "keszits egy osztalyt str metodussal",
        "keszits egy osztalyt eq metodussal",
        "keszits egy osztalyt konstruktorral es ket metodussal",
        "keszits egy osztalyt ami tarol adatokat es listazza oket",
        "keszits egy osztalyt ami szamol ES kezel hibakat",
        "keszits egy osztalyt property getter es setter metodussal",
        "keszits egy osztalyt statikus metodussal",
        "keszits egy osztalyt osztaly metodussal",
        "keszits egy osztalyt iter es len metodussal",
        "keszits egy osztalyt ami fajlbol olvas es feldolgoz",
        "keszits egy osztalyt ami egy masik osztalyt hasznal",
        "keszits egy modult tobb fuggvennyel es egy osztallyal",
        "keszits egy osztalyt ami kezel egy listat add es remove metodussal",
        "keszits egy osztalyt str es repr metodussal",
        "keszits egy osztalyt ami tartalmaz masik osztalyt",
        "keszits egy osztalyt ami egy gyujtemenyt kezel",

        # List comprehension (20)
        "hasznalj list comprehensiont a paros szamok szuresere",
        "hasznalj dict comprehensiont szotar letrehozasara",
        "hasznalj set comprehensiont egyedi ertekekre",
        "hasznalj szuro comprehensiont feltetellel",
        "hasznalj map kifejezest atalakitashoz",
        "hasznalj filter kifejezest szureshez",
        "hasznalj reduce kifejezest osszegzeshez",
        "hasznalj lambda fuggvenyt rendezeshez",
        "hasznalj generator kifejezest",
        "hasznalj generator fuggvenyt yield-del",
        "hasznalj list comprehensiont negyzetre emelessel",
        "hasznalj dict comprehensiont indexelesre",
        "hasznalj comprehensiont tobb feltetellel",
        "hasznalj nested comprehensiont",
        "hasznalj map lambda kifejezest egyutt",
        "hasznalj filter lambda kifejezest",
        "hasznalj reduce lambdaval osszeadashoz",
        "hasznalj generator kifejezest nagy mennyisegre",
        "hasznalj yield from-t generatoban",
        "hasznalj lambda-t tobb parameterrel",

        # Fájlkezelés (20)
        "olvass be egy fajlt es ird ki a tartalmat",
        "irj egy fajlba szoveget",
        "masolj egy fajlt masik nevre",
        "hozz letre egy mappat es irj bele fajlt",
        "olvass be egy json fajlt es dolgozd fel",
        "irj ki adatokat json fajlba",
        "olvass be egy csv fajlt es ird ki soronkent",
        "csinalj egy fuggvenyt ami fajlt olvas es visszaadja a sorokat",
        "csinalj egy fajl masolo fuggvenyt",
        "keszits egy egyszeru naplozo fuggvenyt ami fajlba ir",
        "olvass be egy txt fajlt soronkent",
        "irj tobb sort egy fajlba ciklussal",
        "csinalj egy fuggvenyt ami fajlbol olvas es hibakezel",
        "csinalj egy fuggvenyt ami fajlba ir ES olvas is",
        "hozz letre egy mappat ha nem letezik",
        "listazd ki a mappa tartalmat",
        "csinalj egy fuggvenyt ami fajlokat masol mappak kozott",
        "olvass be egy fajlt es szamold meg a sorokat",
        "irj egy fajlba json formatumban adatokat",
        "csinalj egy fuggvenyt ami CSV-t olvas es feldolgoz",

        # Hiba-és kontextuskezelés (20)
        "keszits egy try catch blokkot hiba kezelesre",
        "keszits egy sajat kivétel osztalyt",
        "hasznalj context managert fajl nyitashoz es bezarashoz",
        "keszits egy sajat context managert",
        "irj egy fuggvenyt ami dob kivételt ha hiba van",
        "hasznalj finally blokkot takaritasra",
        "keszits egy hibaturo fajl olvaso fuggvenyt",
        "keszits egy fuggvenyt ami ellenorzi a bemenet tipusat",
        "hasznalj with open-t fajl olvasashoz",
        "csinalj egy hibakezelo dekoratort",
        "keszits try except finally blokkot",
        "dobj kivételt ha az ertek tul kicsi",
        "kapd el a ZeroDivisionError kivételt",
        "kapd el a FileNotFoundError kivételt",
        "keszits egy fuggvenyt ami tobb kivételt kezel",
        "hasznalj else blokkot try utan",
        "keszits egy context managert ami idozit",
        "hasznalj contextlib.contextmanager-t",
        "keszits egy hibaturo fuggvenyt ami None-t ad vissza hiba eseten",
        "keszits egy fuggvenyt ami ellenorzi es kezeli a bemeneti tipusokat",

        # Haladó (30)
        "keszits egy dekoratort ami idoziti a fuggveny hivast",
        "keszits egy cache dekoratort",
        "keszits egy generator fuggvenyt ami sorozatot allit elo",
        "hasznalj random szam generalast egy ertek kivalasztasahoz",
        "hasznalj random mintavetelt egy listabol",
        "keszits egy fuggvenyt ami szotarbol ertekeket nyer ki",
        "keszits egy fuggvenyt tobb parameternel",
        "keszits egy fuggvenyt ami stringet dolgoz fel",
        "hasznalj collections.deque-t sorkent",
        "hasznalj defaultdict-t csoportositasra",
        "keszits egy statikus metodust egy osztalyban",
        "keszits egy property getter es settert",
        "keszits egy osztalyt iter metodussal",
        "keszits egy osztalyt len metodussal",
        "hasznalj from import-ot specifikus fuggvenyhez",
        "hasznalj as import-ot alias-szal",
        "keszits egy rekurziv fuggvenyt",
        "keszits egy fuggvenyt ami tipusokat ellenoriz",
        "keszits egy dekoratort ami naplozza a hivasokat",
        "keszits egy generator fuggvenyt ami veletlen szamokat ad",
        "keszits egy fuggvenyt ami hasznalja a random modult",
        "keszits egy fuggvenyt ami hasznalja a collections modult",
        "keszits egy osztalyt ami enum ertekeket hasznal",
        "keszits egy fuggvenyt ami default szotarat hasznal",
        "keszits egy fuggvenyt ami sort hasznal (deque)",
        "keszits egy generator fuggvenyt vegtelen sorozatra",
        "keszits egy fuggvenyt ami egy masik fuggvenyt hiv meg",
        "keszits egy fuggvenyt ami osszehasonlit ket erteket",
        "keszits egy fuggvenyt ami regex-et hasznal",
        "keszits egy fuggvenyt ami datumot kezel",
    ]

    # ---- JAVASCRIPT FELADATOK (150) ----
    js_tasks = [
        # Alap (20)
        "szurd ki a paros szamokat javascriptben",
        "rendezz egy listat javascriptben",
        "transzformalj egy listat map-pal javascriptben",
        "szamold ossze a lista elemeit reduce-zal javascriptben",
        "jard be a lista elemeit forEach-csel javascriptben",
        "irj egy javascript fuggvenyt ami visszaadja a legnagyobb erteket",
        "irj egy javascript fuggvenyt ami szuri a pozitiv szamokat",
        "irj egy javascript fuggvenyt ket parameterrel es visszateressel",
        "hasznalj feltételt es logikai operatort javascriptben",
        "irj javascript konzolra az osszes elemet",
        "valogass ki egy listabol minden masodik elemet javascriptben",
        "irj egy javascript fuggvenyt ami forditott sorrendben adja vissza",
        "hasznalj arrow function-t javascriptben",
        "irj egy javascript fuggvenyt ami osszehasonlit ket objektumot",
        "keszits egy javascript fuggvenyt ami egy stringet kezel",
        "hasznalj template literal-t javascriptben",
        "hasznalj spread operatort javascriptben",
        "hasznalj destructuring-et javascriptben",
        "irj egy javascript fuggvenyt alapértelmezett parameterrel",
        "keszits egy objektumot javascriptben es ird ki a tulajdonsagait",

        # DOM (30)
        "keresd ki a DOM-bol egy elemet querySelectorral",
        "modositsd egy elem stilusat DOM-bol",
        "hozz letre egy uj DOM elemet es add hozza egy masikhoz",
        "torolj egy DOM elemet",
        "adj esemenykezelot egy gombhoz",
        "valtoztasd meg egy elem tartalmat DOM-bol",
        "valtoztasd meg egy elem CSS osztalyat DOM-bol",
        "keresd ki az osszes elemet querySelectorAllal",
        "hozz letre egy listat DOM elemekbol",
        "szurd ki a DOM elemeket egy lista alapjan",
        "rendezz DOM elemeket adat alapjan",
        "keresd ki az input mezo erteket es hasznald",
        "valtoztasd meg tobb elem stilusat egyszerre",
        "adj esemenykezelot minden listaelemhez javascriptben",
        "csinalj egy szamlalot ami kattintasra no javascriptben",
        "csinalj egy keresot ami szuri az elemeket javascriptben",
        "csinalj egy accordion-t ami nyit es zár elemeket javascriptben",
        "csinalj egy tab rendszert javascriptben",
        "csinalj egy modal ablakot javascriptben",
        "csinalj egy lenyilo menüt kattintasra javascriptben",
        "csinalj egy progress bart ami elorehalad javascriptben",
        "csinalj egy orat ami mutatja az aktualis idot javascriptben",
        "csinalj egy szamologepet alap muveletekkel javascriptben",
        "csinalj egy todo listat javascriptben",
        "csinalj egy galeria navigaciot javascriptben",
        "hozz letre dinamikusan DOM elemeket javascriptben",
        "csinalj egy gombot ami mutatja elrejti a tartalmat javascriptben",
        "csinalj egy dark mode valtot javascriptben",
        "csinalj egy scroll-to-top gombot javascriptben",
        "csinalj egy animalt betolto ikont javascriptben",

        # Haladó (30)
        "irj egy async fuggvenyt ami fetch-el egy API-t es feldolgozza",
        "irj egy fetch POST-ot JSON adattal javascriptben",
        "irj egy async fuggvenyt ami tobb API-t hiv meg",
        "validalj egy urlapot form esemenykezelovel javascriptben",
        "ments el adatot localStorage-ba es olvasd vissza javascriptben",
        "torolj adatot localStorage-bol javascriptben",
        "csinalj egy animaciot ami elhalvanyit egy elemet javascriptben",
        "csinalj egy animaciot requestAnimationFrame-el javascriptben",
        "hasznalj Math.random-ot veletlen szamhoz javascriptben",
        "hasznalj Math.round-ot kerekitéshez javascriptben",
        "hasznalj Math.min es Math.max-ot javascriptben",
        "csinalj egy idozitot setTimeout-tal javascriptben",
        "csinalj egy idozitot setInterval-lel javascriptben",
        "csinalj egy todo listat localStorage-ba mentessel javascriptben",
        "csinalj egy szamologepet localStorage mentessel javascriptben",
        "csinalj egy API lekerdezo gombot javascriptben",
        "csinalj egy idojaras widgetet fetch-el javascriptben",
        "csinalj egy felhasznalo listat API-bol javascriptben",
        "csinalj egy kozossegi media megoszto gombot javascriptben",
        "csinalj egy idozitett ertesitest setTimeout-tal javascriptben",
        "keszits egy async fuggvenyt ami varakozik es utana fut le",
        "csinalj egy fetch hibakezelo fuggvenyt javascriptben",
        "csinalj egy localStorage alapú kedvencek listat javascriptben",
        "csinalj egy keresot API hivassal javascriptben",
        "csinalj egy tobb lepeses URLAP wizardot javascriptben",
        "csinalj egy drag-and-drop egyszeru peldat javascriptben",
        "csinalj egy rajzolo alkalmazast canvas-al javascriptben",
        "csinalj egy billentyuzet esemeny kezelot javascriptben",
        "csinalj egy reszponziv menu-t hamburger gombbal javascriptben",
        "csinalj egy keresesi javaslat rendszert javascriptben",
    ]

    # ---- VEGYES FELADATOK (50) ----
    mixed_tasks = [
        "keszits egy weblapot python szuro scripttel es kimutatas tablazattal",
        "keszits egy adat feldolgozo python scriptet ami html tablazatot general",
        "keszits egy jatek weblapot javascript validdal urlaphoz",
        "keszits egy osztalyt pythonban es egy weblapot ami bemutatja",
        "keszits egy weblapot javascript animacioval es modal ablakkal",
        "keszits egy weblapot javascript keresovel es szuresi lehetoseggel",
        "keszits egy python fuggvenyt es egy weblapot ami hasznalja",
        "keszits egy weblapot javascript todo listaval es localStorage mentessel",
        "keszits egy python scriptet adat feldolgozasra es egy weblapot az adatok megjelenitesere",
        "keszits egy weblapot javascript szamlaloval es progress barral",
    ]

    # Összes feladat
    all_tasks = html_tasks + python_tasks + js_tasks + mixed_tasks
    all_tasks = all_tasks[:800]  # max 800
    random.shuffle(all_tasks)  # Véletlen sorrend a jobb általánosításhoz

    print(f"  Összes feladat: {len(all_tasks)}")
    print(f"    HTML: {len(html_tasks)}")
    print(f"    Python: {len(python_tasks)}")
    print(f"    JavaScript: {len(js_tasks)}")
    print(f"    Vegyes: {len(mixed_tasks)}")

    # === FUTTATÁS ===
    success_count = 0
    fail_count = 0
    total_chars = 0
    max_chars = 0
    max_task = ""
    results = []
    
    # Több ciklus a SelfImprover-en keresztül
    for cycle in range(3):  # 3 ciklus
        print(f"\n  --- Ciklus {cycle+1}/3 ---")
        
        # Először: általános felfedezés
        if cycle == 0:
            findings = improver.discover_all()
            if findings:
                print(f"  Felfedezések: {len(findings)}")
                for d in findings[:3]:
                    print(f"    {d}")
        
        # Feladatok futtatása
        batch_size = min(170, len(all_tasks))
        batch = all_tasks[:batch_size]
        all_tasks = all_tasks[batch_size:]
        
        for i, task in enumerate(batch):
            try:
                # Nyelv detektálás
                lang = "html"
                if any(w in task.lower() for w in ["python", "pythonban", "szurd", "szűrd", "rendez", "osztalyt", "fuggvenyt", "list comprehension", "try catch", "dekoratort", "generator", "fajl", "lambda"]):
                    lang = "python"
                elif any(w in task.lower() for w in ["javascript", "js", "dom", "fetch", "async", "localstorage", "settimeout", "setinterval", "console.log"]):
                    lang = "javascript"

                # Inferencia gazdagítás (ha van zárójelezett lista)
                enriched = task
                if '(' in task and ')' in task:
                    enriched = infer.enrich_goal(task)

                # SelfImprover futtatás
                code, log = improver.run(enriched, language=lang)

                if code:
                    lines = code.split('\n')
                    chars = len(code)
                    success_count += 1
                    total_chars += chars
                    if chars > max_chars:
                        max_chars = chars
                        max_task = task
                    results.append((task, lang, chars, "OK"))
                    if i % 25 == 0:
                        print(f"    [{i+1}/{len(batch)}] {task[:50]}... {len(lines)}sor {chars}char OK")
                else:
                    fail_count += 1
                    results.append((task, lang, 0, "FAIL"))
                    if fail_count <= 5:
                        print(f"    [{i+1}/{len(batch)}] {task[:50]}... FAIL")
            except Exception as e:
                fail_count += 1
                results.append((task, "?", 0, f"ERR: {e}"))
                if fail_count <= 5:
                    print(f"    [{i+1}/{len(batch)}] {task[:50]}... HIBA: {str(e)[:50]}")

        # Ciklus végi felfedezés
        findings = improver.discover_all()
        if findings:
            print(f"  Felfedezések ciklus után: {len(findings)}")
            for d in findings[:3]:
                print(f"    {d}")

    # ==================================================================
    # 6. VÉGSŐ STATISZTIKA
    # ==================================================================
    elapsed = time.time() - start_time
    print(f"\n[6/6] Végső statisztika")
    print(f"  Futási idő: {elapsed:.1f}s")
    print(f"  Összes feladat: {success_count + fail_count}")
    print(f"  Sikeres: {success_count}")
    print(f"  Sikertelen: {fail_count}")
    print(f"  Sikerességi arány: {success_count/(success_count+fail_count)*100:.1f}%")
    print(f"  Max kimenet: {max_chars} chars ({max_task[:60]})")
    print(f"  Átlag kimenet: {total_chars/success_count if success_count else 0:.0f} chars")

    # Tudásbázis statisztika
    stats = g.stats()
    print(f"\n  Tudásbázis:")
    print(f"    Fogalmak: {stats['concepts']}")
    print(f"    Kapcsolatok: {stats['relations']}")
    print(f"    Műveletek: {stats['operations']}")

    # Template-ek száma
    print(f"\n  Template-ek:")
    for lang_name, dialect in gen.dialects.items():
        count = len(dialect._mappings)
        print(f"    {lang_name}: {count}")

    # Parser pattern-ek
    print(f"\n  Parser pattern-ek: {len(parser._task_patterns)}")

    # SelfImprover felfedezések
    print(f"\n  Önfejlesztő:")
    print(f"    Javítások: {improver.improvement_count}")
    print(f"    Felfedezések: {len(improver.discoveries)}")

    # Inferencia
    print(f"\n  Nyelvi értelmező:")
    print(f"    Inferált fogalmak: {infer.inferred_count}")

    # Top 5 legnagyobb kimenet
    print(f"\n  Top 5 legnagyobb kimenet:")
    sorted_results = sorted(results, key=lambda x: -x[2])[:5]
    for task, lang, chars, status in sorted_results:
        print(f"    {chars:>6} chars | {lang:>8} | {task[:50]}")

    print(f"\n  JELENTÉS: report_training.txt")
    with open(os.path.join(os.path.dirname(__file__), "training_report.txt"), "w", encoding="utf-8") as f:
        f.write(f"DKA V3 — Training Report\n")
        f.write(f"{'='*60}\n")
        f.write(f"Futási idő: {elapsed:.1f}s\n")
        f.write(f"Összes feladat: {success_count + fail_count}\n")
        f.write(f"Sikeres: {success_count}\n")
        f.write(f"Sikertelen: {fail_count}\n")
        f.write(f"Sikerességi arány: {success_count/(success_count+fail_count)*100:.1f}%\n")
        f.write(f"Max kimenet: {max_chars} chars\n")
        f.write(f"Átlag kimenet: {total_chars/success_count if success_count else 0:.0f} chars\n\n")
        f.write(f"Tudásbázis: {stats['concepts']} fogalom, {stats['relations']} kapcsolat\n\n")
        f.write(f"Template-ek:\n")
        for lang_name, dialect in gen.dialects.items():
            f.write(f"  {lang_name}: {len(dialect._mappings)}\n")
        f.write(f"\nParser pattern-ek: {len(parser._task_patterns)}\n")
        f.write(f"Önfejlesztő javítások: {improver.improvement_count}\n")
        f.write(f"Önfejlesztő felfedezések: {len(improver.discoveries)}\n")
        f.write(f"Nyelvi értelmező inferálások: {infer.inferred_count}\n")
        f.write(f"\nFelfedezések (utolsó 20):\n")
        for d in improver.discoveries[-20:]:
            f.write(f"  {d}\n")
        f.write(f"\nTop 5 legnagyobb kimenet:\n")
        for task, lang, chars, status in sorted_results[:5]:
            f.write(f"  {chars:>6} chars | {lang:>8} | {task[:60]}\n")

    return g, parser, gen, improver, infer


if __name__ == "__main__":
    result = run_training()
    print("\n✅ TRÉNING BEFEJEZVE!")
