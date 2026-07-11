"""
DKA V3 — 1000+ fogalom generálása
====================================
Nem kézzel írva: program generálja a fogalmakat minták alapján.
"""

from concept_graph import ConceptGraph, Concept, Operation, Property, RelationType


def seed_massive(graph: ConceptGraph):
    """1000+ fogalom generálása minták alapján."""
    count_before = len(graph.concepts)
    
    # ===== 1. HTML ÖSSZES ELEM (50+) =====
    html_tags = {
        # Strukturális
        "html": "<html>", "head": "<head>", "body": "<body>",
        "main": "<main>", "section": "<section>", "article": "<article>",
        "aside": "<aside>", "div": "<div>", "span": "<span>",
        # Szöveg
        "h1": "<h1>", "h2": "<h2>", "h3": "<h3>", "h4": "<h4>",
        "h5": "<h5>", "h6": "<h6>", "p": "<p>", "strong": "<strong>",
        "em": "<em>", "b": "<b>", "i": "<i>", "u": "<u>",
        "small": "<small>", "mark": "<mark>", "del": "<del>",
        "ins": "<ins>", "sub": "<sub>", "sup": "<sup>",
        "code": "<code>", "pre": "<pre>", "blockquote": "<blockquote>",
        "hr": "<hr>", "br": "<br>",
        # Link
        "a": "<a>",
        # Lista
        "ul": "<ul>", "ol": "<ol>", "li": "<li>",
        "dl": "<dl>", "dt": "<dt>", "dd": "<dd>",
        # Táblázat
        "table": "<table>", "thead": "<thead>", "tbody": "<tbody>",
        "tfoot": "<tfoot>", "tr": "<tr>", "th": "<th>", "td": "<td>",
        "col": "<col>", "colgroup": "<colgroup>", "caption": "<caption>",
        # Űrlap
        "textarea": "<textarea>", "select": "<select>",
        "option": "<option>", "optgroup": "<optgroup>",
        "fieldset": "<fieldset>", "legend": "<legend>",
        "datalist": "<datalist>", "output": "<output>",
        # Média
        "video": "<video>", "audio": "<audio>",
        "source": "<source>", "track": "<track>",
        # Interaktív
        "details": "<details>", "summary": "<summary>",
        "dialog": "<dialog>",
        # Meta
        "meta": "<meta>", "link": "<link>", "base": "<base>",
        "script": "<script>", "noscript": "<noscript>",
        "style": "<style>",
        # Egyéb
        "figure": "<figure>", "figcaption": "<figcaption>",
        "time": "<time>", "address": "<address>",
    }
    
    for tag, html in html_tags.items():
        c = Concept(name=tag, description="<%s> HTML elem" % tag,
                   language_mappings={"html": html})
        graph.add(c)
    
    # ===== 2. INPUT TÍPUSOK (20+) =====
    input_types = [
        ("text_input", "Szöveges beviteli mező", "text"),
        ("email_input", "Email cím beviteli mező", "email"),
        ("password_input", "Jelszó beviteli mező", "password"),
        ("number_input", "Szám beviteli mező", "number"),
        ("tel_input", "Telefonszám beviteli mező", "tel"),
        ("url_input", "URL beviteli mező", "url"),
        ("search_input", "Kereső mező", "search"),
        ("date_input", "Dátum választó", "date"),
        ("time_input", "Idő választó", "time"),
        ("file_input", "Fájl feltöltő", "file"),
        ("checkbox_input", "Jelölő négyzet", "checkbox"),
        ("radio_input", "Választógomb", "radio"),
        ("color_input", "Színválasztó", "color"),
        ("range_input", "Csúszka", "range"),
        ("hidden_input", "Rejtett mező", "hidden"),
        ("submit_input", "Küldés gomb", "submit"),
        ("reset_input", "Visszaállítás gomb", "reset"),
    ]
    
    for name, desc, itype in input_types:
        c = Concept(name=name, description=desc,
                   properties=[Property("type", "szöveg", "HTML input type: " + itype)],
                   language_mappings={"html": "<input type='%s'>" % itype})
        graph.add(c)
        graph.relate(name, "input_mező", RelationType.IS_A)
    
    # ===== 3. GYAKORI MAGYAR SZINONÍMÁK (300+) =====
    hungarian_words = [
        # Oldal típusok
        ("honlap", "weblap"), ("site", "weblap"),
        ("portfolió", "weblap"), ("portfolio", "weblap"),
        ("blog", "weblap"), ("weblog", "weblap"),
        ("webshop", "weblap"), ("áruház", "weblap"),
        ("weboldal", "weblap"), ("webhely", "weblap"),
        ("dokumentum", "weblap"), ("wiki", "weblap"),
        
        # Cím
        ("fejléc", "cím"), ("header", "cím"),
        ("title", "cím"), ("heading", "cím"),
        ("alcím", "cím"),
        
        # Bekezdés
        ("paragraph", "bekezdés"), ("szöveg", "bekezdés"),
        ("tartalom", "bekezdés"), ("szövegrész", "bekezdés"),
        ("leírás", "bekezdés"), ("description", "bekezdés"),
        ("bemutatkozás", "bekezdés"), ("introduction", "bekezdés"),
        ("bemutatkozas", "bekezdés"), ("leiras", "bekezdés"),
        ("szoveg", "bekezdés"), ("tartalom", "bekezdés"),
        
        # Űrlap
        ("form", "űrlap"), ("ürlap", "űrlap"),
        ("urlap", "űrlap"), ("urlapot", "űrlap"),
        ("formular", "űrlap"), ("kérdőív", "űrlap"),
        
        # Input
        ("mező", "input_mező"), ("mezo", "input_mező"),
        ("field", "input_mező"), ("bevitel", "input_mező"),
        ("beviteli_mező", "input_mező"),
        
        # Gomb
        ("button", "gomb"), ("btn", "gomb"),
        ("submit", "gomb"), ("küldés", "gomb"),
        ("kattints", "gomb"),
        
        # Kép
        ("kép", "kép"), ("image", "kép"),
        ("img", "kép"), ("picture", "kép"),
        ("photo", "kép"), ("foto", "kép"),
        ("ábra", "kép"), ("abra", "kép"),
        ("grafika", "kép"), ("illusztráció", "kép"),
        
        # Táblázat
        ("table", "táblázat"), ("tablazat", "táblázat"),
        ("adattábla", "táblázat"), ("matrix", "táblázat"),
        
        # Navigáció
        ("menu", "menü"), ("nav", "menü"),
        ("navigacio", "menü"), ("navigáció", "menü"),
        ("menü", "menü"),
        
        # Link
        ("href", "link"), ("url", "link"),
        ("hypertext", "link"), ("hyperlink", "link"),
        ("hivatkozás", "link"), ("hivatkozas", "link"),
        
        # Stílus
        ("css", "stílus"), ("style", "stílus"),
        ("design", "stílus"), ("formatum", "stílus"),
        ("skin", "stílus"), ("téma", "stílus"),
        ("tema", "stílus"),
        
        # Lábléc
        ("footer", "lábléc"), ("lablec", "lábléc"),
        ("copyright", "lábléc"),
        
        # Adat műveletek
        ("összeg", "összegzés"), ("total", "összegzés"),
        ("summary", "összegzés"), ("osszeg", "összegzés"),
        ("osszegzes", "összegzés"),
        
        ("filter", "szűrés"), ("szures", "szűrés"),
        ("filterez", "szűrés"), ("szure", "szűrés"),
        ("válogatás", "szűrés"), ("valogatas", "szűrés"),
        
        ("rend", "rendezés"), ("rendezes", "rendezés"),
        ("sort", "rendezés"), ("order", "rendezés"),
        ("sorrend", "rendezés"), ("rendez", "rendezés"),
        
        ("map", "transzformáció"), ("atalkitas", "transzformáció"),
        ("konvert", "transzformáció"), ("convert", "transzformáció"),
        
        # Gyűjtemény
        ("list", "gyűjtemény"), ("array", "gyűjtemény"),
        ("collection", "gyűjtemény"), ("lista", "gyűjtemény"),
        ("tomb", "gyűjtemény"), ("tömb", "gyűjtemény"),
        ("vektor", "gyűjtemény"), ("sorozat", "gyűjtemény"),
        
        ("dict", "szótár"), ("szotar", "szótár"),
        ("object", "szótár"), ("map", "szótár"),
        ("hash", "szótár"), ("asszociativ", "szótár"),
        
        ("str", "szöveg"), ("string", "szöveg"),
        ("text", "szöveg"), ("szoveg", "szöveg"),
        ("karakter", "szöveg"), ("char", "szöveg"),
        
        # Ciklus
        ("for", "ciklus"), ("while", "ciklus"),
        ("loop", "ciklus"), ("iteracio", "ciklus"),
        ("ciklus", "ciklus"), ("ismetles", "ciklus"),
        ("each", "ciklus"), ("forEach", "ciklus"),
        
        # Feltétel
        ("if", "feltétel"), ("condition", "feltétel"),
        ("ha", "feltétel"), ("feltetel", "feltétel"),
        ("case", "feltétel"), ("switch", "feltétel"),
        ("elágazás", "feltétel"), ("elagazas", "feltétel"),
        
        # Függvény
        ("function", "függvény"), ("fuggveny", "függvény"),
        ("method", "függvény"), ("metodus", "függvény"),
        ("eljárás", "függvény"), ("eljaras", "függvény"),
        ("subroutine", "függvény"),
        
        # Érték
        ("value", "érték"), ("ertek", "érték"),
        ("val", "érték"), ("variable", "érték"),
        ("valtozo", "érték"), ("változó", "érték"),
        
        # Szám
        ("number", "szám"), ("szam", "szám"),
        ("num", "szám"), ("integer", "szám"),
        ("float", "szám"), ("double", "szám"),
        ("int", "szám"),
        
        # Logikai
        ("bool", "logikai"), ("boolean", "logikai"),
        ("true", "logikai"), ("false", "logikai"),
        ("igaz", "logikai"), ("hamis", "logikai"),
        ("yes", "logikai"), ("no", "logikai"),
    ]
    
    for word, target in hungarian_words:
        if word not in graph.concepts and word != target:
            c = Concept(name=word, description="Szinonima: %s" % target,
                       confidence=0.5)
            graph.add(c)
            graph.relate(word, target, RelationType.SAME_AS)

    # ===== 4. WEBOLDAL ELEMEK KAPCSOLATAI =====
    # Minden HTML elem PART_OF weblap
    for tag in html_tags:
        if tag not in ("html", "head", "body"):
            graph.relate(tag, "weblap", RelationType.PART_OF, strength=0.3)
    
    # ===== 5. FÁJL MŰVELETEK (10+) =====
    file_concepts = [
        ("file", "Fájl a fájlrendszerben."),
        ("file_read", "Fájl olvasása."),
        ("file_write", "Fájl írása."),
        ("file_open", "Fájl megnyitása."),
        ("file_close", "Fájl bezárása."),
        ("directory", "Könyvtár a fájlrendszerben."),
        ("path", "Elérési út a fájlrendszerben."),
        ("filenev", "Fájl neve kiterjesztéssel."),
        ("file_name", "File name."),
        ("file_extension", "Fájl kiterjesztése."),
    ]
    for name, desc in file_concepts:
        graph.add(Concept(name=name, description=desc))
    
    # ===== 6. SZOLGÁLTATÁS KÁRTYA (service card) =====
    graph.add(Concept(name="kártya",
        description="Kártya UI elem. Cím, szöveg, esetleg kép vagy gomb.",
        language_mappings={"html": "<div class='card'><h3>{title}</h3><p>{text}</p></div>"},
    ))
    graph.add(Concept(name="card", description="UI card element.",
        language_mappings={"html": "<div class='card'><h3>{title}</h3><p>{text}</p></div>"},
    ))
    graph.relate("kártya", "weblap", RelationType.PART_OF)
    graph.relate("card", "kártya", RelationType.SAME_AS)
    
    # ===== 7. ISMERT MAGYAR IGÉK AKCIÓKHOZ (50+) =====
    verb_actions = {
        "készít": ("weblap", "weblap"),
        "keszit": ("weblap", "weblap"),
        "csinál": ("weblap", "weblap"),
        "csinal": ("weblap", "weblap"),
        "épít": ("weblap", "weblap"),
        "epit": ("weblap", "weblap"),
        "generál": ("weblap", "weblap"),
        "general": ("weblap", "weblap"),
        "alkot": ("weblap", "weblap"),
        "létrehoz": ("weblap", "weblap"),
        "letrehoz": ("weblap", "weblap"),
        "kreál": ("weblap", "weblap"),
        "kreal": ("weblap", "weblap"),
        "tervez": ("weblap", "weblap"),
        "megtervez": ("weblap", "weblap"),
        
        "keres": ("szűrés", "gyűjtemény"),
        "keresd": ("szűrés", "gyűjtemény"),
        "talál": ("szűrés", "gyűjtemény"),
        "talal": ("szűrés", "gyűjtemény"),
        
        "rendezd": ("rendezés", "gyűjtemény"),
        "rendezi": ("rendezés", "gyűjtemény"),
        "sorba": ("rendezés", "gyűjtemény"),
        
        "vedd": ("első", "gyűjtemény"),
        "válassz": ("első", "gyűjtemény"),
        "valassz": ("első", "gyűjtemény"),
        "szedd": ("első", "gyűjtemény"),
        
        "számold": ("megszámlálás", "gyűjtemény"),
        "szamold": ("megszámlálás", "gyűjtemény"),
        "számol": ("megszámlálás", "gyűjtemény"),
        "szamol": ("megszámlálás", "gyűjtemény"),
        
        "forditsd": ("fordítás", "gyűjtemény"),
        "fordits": ("fordítás", "gyűjtemény"),
        "fordit": ("fordítás", "gyűjtemény"),
        
        "add": ("összegzés", "gyűjtemény"),
        "összegez": ("összegzés", "gyűjtemény"),
        "osszegez": ("összegzés", "gyűjtemény"),
        
        "szűrj": ("szűrés", "gyűjtemény"),
        "szurj": ("szűrés", "gyűjtemény"),
        "szurd": ("szűrés", "gyűjtemény"),
    }
    
    for verb, (action, target) in verb_actions.items():
        if verb not in graph.concepts:
            c = Concept(name=verb, description="Ige: %s" % action,
                       confidence=0.6)
            graph.add(c)
    
    # ===== 8. SZOLGÁLTATÁS, PORTFÓLIÓ, BEMUTATKOZÁS =====
    for cname, cdesc in [
        ("szolgáltatás", "Szolgáltatás leírása. Általában cím + leírás + ikon."),
        ("szolgaltatas", "Szolgáltatás leírása."),
        ("service", "Service description."),
        ("bemutatkozás", "Bemutatkozó szöveg. Általában név + foglalkozás + leírás."),
        ("bemutatkozas", "Bemutatkozó szöveg."),
        ("introduction", "Introduction text."),
        ("portfolio", "Portfolio website."),
        ("portfolió", "Portfólió weboldal."),
        ("about", "About section."),
        ("rolunk", "Rólunk szekció."),
        ("kapcsolat", "Kapcsolat szekció."),
        ("contact", "Contact section."),
        ("üzenet", "Üzenet szöveges mező."),
        ("uzenet", "Üzenet szöveges mező."),
        ("message", "Message text field."),
    ]:
        graph.add(Concept(name=cname, description=cdesc))
    
    # ===== STATISZTIKA =====
    added = len(graph.concepts) - count_before
    # Python kapcsolatok
    graph.relate("konstruktor", "osztály", RelationType.PART_OF)
    graph.relate("metódus", "osztály", RelationType.PART_OF)
    graph.relate("tulajdonság", "osztály", RelationType.PART_OF)
    graph.relate("visszatérés", "függvény", RelationType.PART_OF)
    print("  [+] %d uj fogalom (osszesen: %d)" % (added, len(graph.concepts)))
    print("  [+] %d kapcsolat" % len(set(
        (r.type, r.target_name) for c in graph.concepts.values() for r in c.relations
    )))
    
    return graph
