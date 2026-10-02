"""
Beispieldatensätze für die Vektordatenbank-Demo.
Format passt zur Collection `space_objects`: Name + Beschreibung (+ user_id beim Import).
Struktur: DEMO_DATEN[cluster] = [(name, beschreibung), ...]
Bewusst: Beschreibungen mit 1-2 vollständigen Sätzen, damit das Embedding-Modell
(paraphrase-multilingual-MiniLM-L12-v2) semantisch sauber trennt.
"""

DEMO_DATEN = {
    "Berufe – Bildung": [
        ("Grundschullehrerin", "Unterrichtet Kinder im Alter von sechs bis zehn Jahren in Lesen, Schreiben und Rechnen."),
        ("Mathelehrer", "Erklärt Schülern am Gymnasium Algebra, Geometrie und Analysis und korrigiert Klassenarbeiten."),
        ("Professorin", "Forscht an der Universität, hält Vorlesungen und betreut Doktoranden."),
        ("Erzieher", "Betreut Kinder in der Kita, spielt, bastelt und fördert ihre Entwicklung."),
        ("Schulleiter", "Leitet die Schule, organisiert den Stundenplan und führt das Kollegium."),
        ("Nachhilfelehrer", "Hilft Schülern am Nachmittag, Lücken in Mathe und Englisch zu schließen."),
        ("Dozent", "Unterrichtet Studierende in Seminaren und bereitet Prüfungen vor."),
        ("Schulsozialarbeiterin", "Berät Schüler bei Problemen und vermittelt zwischen Eltern und Lehrkräften."),
    ],
    "Berufe – Handwerk & Industrie": [
        ("Schreiner", "Fertigt Möbel und Türen aus Holz und arbeitet mit Hobel, Säge und Schleifmaschine."),
        ("Elektriker", "Installiert Stromleitungen, Steckdosen und Sicherungskästen in Gebäuden."),
        ("Maurer", "Baut Wände aus Ziegeln und Mörtel auf der Baustelle."),
        ("Schweißer", "Verbindet Metallteile durch Schweißen in der Fabrikhalle."),
        ("Fließbandarbeiter", "Montiert in der Produktion Bauteile am Fließband im Schichtbetrieb."),
        ("Klempner", "Repariert Wasserleitungen, Heizungen und verstopfte Abflüsse."),
        ("Lagerarbeiter", "Kommissioniert Waren, bedient den Gabelstapler und verlädt Paletten."),
        ("Kfz-Mechatroniker", "Wartet und repariert Autos in der Werkstatt, tauscht Bremsen und Reifen."),
    ],
    "Berufe – Büro & IT": [
        ("Softwareentwickler", "Schreibt Programmcode, testet Anwendungen und arbeitet mit Git im Team."),
        ("Data Scientist", "Wertet große Datenmengen aus und trainiert Modelle für maschinelles Lernen."),
        ("Buchhalterin", "Verbucht Rechnungen, erstellt Bilanzen und bereitet die Steuererklärung vor."),
        ("Projektmanager", "Plant Budgets und Termine und koordiniert das Projektteam."),
        ("Systemadministrator", "Betreibt Server und Netzwerke und behebt IT-Störungen."),
        ("Personalreferentin", "Führt Bewerbungsgespräche und kümmert sich um Verträge der Mitarbeitenden."),
        ("UX-Designer", "Gestaltet Oberflächen für Apps und testet sie mit echten Nutzern."),
        ("Sachbearbeiter", "Bearbeitet Anträge und Schriftverkehr im Büro."),
    ],
    "Berufe – Gesundheit": [
        ("Krankenpfleger", "Versorgt Patienten auf der Station, verteilt Medikamente und misst Vitalwerte."),
        ("Hausärztin", "Untersucht Patienten in der Praxis, stellt Diagnosen und schreibt Rezepte."),
        ("Chirurg", "Operiert Patienten im Operationssaal."),
        ("Physiotherapeutin", "Behandelt Verspannungen und Verletzungen mit Massage und Übungen."),
        ("Zahnarzt", "Behandelt Karies, zieht Zähne und führt Vorsorgeuntersuchungen durch."),
        ("Apothekerin", "Berät Kunden zu Medikamenten und gibt verschreibungspflichtige Arzneimittel aus."),
        ("Rettungssanitäter", "Versorgt Notfallpatienten im Rettungswagen und fährt sie ins Krankenhaus."),
        ("Hebamme", "Begleitet Frauen während Schwangerschaft und Geburt."),
    ],
    "Obst": [
        ("Apfel", "Knackige, süß-säuerliche Frucht, die am Baum wächst und roh oder als Kuchen gegessen wird."),
        ("Banane", "Gebogene gelbe Frucht mit weichem, süßem Fruchtfleisch aus den Tropen."),
        ("Erdbeere", "Kleine rote Beere mit aromatischem Duft, Saison im Frühsommer."),
        ("Orange", "Saftige Zitrusfrucht mit dicker Schale und viel Vitamin C."),
        ("Weintraube", "Kleine süße Früchte in Trauben, Grundlage für Wein und Rosinen."),
        ("Mango", "Tropische Steinfrucht mit orangefarbenem, sehr süßem Fruchtfleisch."),
        ("Birne", "Saftige Frucht mit weichem Fruchtfleisch und leicht körnigem Geschmack."),
        ("Kirsche", "Kleine rote Steinfrucht mit süßem bis säuerlichem Geschmack."),
        ("Ananas", "Große tropische Frucht mit stacheliger Schale und säuerlich-süßem Fruchtfleisch."),
        ("Blaubeere", "Kleine dunkelblaue Beere, wächst am Strauch und färbt beim Essen die Zunge."),
    ],
    "Gemüse": [
        ("Karotte", "Orangefarbene Wurzel, knackig und süßlich, roh oder gekocht essbar."),
        ("Brokkoli", "Grünes Kohlgemüse mit kleinen Röschen, wird gedünstet gegessen."),
        ("Kartoffel", "Stärkehaltige Knolle, die im Boden wächst und als Beilage gekocht oder gebraten wird."),
        ("Zwiebel", "Würzige Knolle, die beim Schneiden die Augen tränen lässt."),
        ("Spinat", "Dunkelgrünes Blattgemüse mit viel Eisen, wird gedünstet oder als Salat gegessen."),
        ("Paprika", "Hohles Gemüse in Rot, Gelb oder Grün mit mildem bis scharfem Geschmack."),
        ("Gurke", "Langes grünes Gemüse mit hohem Wasseranteil, frisch im Salat."),
        ("Blumenkohl", "Weißes Kohlgemüse mit dichtem Kopf, wird gekocht oder überbacken."),
        ("Zucchini", "Längliches grünes Sommergemüse, wird gebraten oder gegrillt."),
        ("Knoblauch", "Scharfe Knolle mit intensivem Geruch zum Würzen von Speisen."),
    ],
    "Möbel": [
        ("Esstisch", "Großer Holztisch im Esszimmer, an dem die Familie gemeinsam isst."),
        ("Sofa", "Gepolsterte Sitzgelegenheit im Wohnzimmer für mehrere Personen."),
        ("Bücherregal", "Offenes Regal mit mehreren Böden zum Aufstellen von Büchern."),
        ("Kleiderschrank", "Großer Schrank im Schlafzimmer mit Stange und Fächern für Kleidung."),
        ("Bett", "Möbelstück mit Matratze zum Schlafen im Schlafzimmer."),
        ("Schreibtisch", "Arbeitstisch mit Schubladen, auf dem Computer und Unterlagen stehen."),
        ("Bürostuhl", "Höhenverstellbarer Drehstuhl mit Rollen für langes Sitzen am Schreibtisch."),
        ("Sideboard", "Niedriger Schrank im Wohnzimmer zur Aufbewahrung von Geschirr und Dekoration."),
        ("Nachttisch", "Kleiner Tisch neben dem Bett mit Schublade für Lampe und Wecker."),
        ("Garderobe", "Möbel im Flur mit Haken und Ablage für Jacken und Schuhe."),
    ],
    "Werkzeuge": [
        ("Hammer", "Schlagwerkzeug mit schwerem Kopf, mit dem Nägel in Holz getrieben werden."),
        ("Schraubendreher", "Werkzeug mit Griff und Klinge zum Eindrehen und Lösen von Schrauben."),
        ("Akkuschrauber", "Elektrisches Handgerät zum schnellen Schrauben und Bohren."),
        ("Zange", "Greifwerkzeug zum Festhalten, Biegen und Durchtrennen von Draht."),
        ("Säge", "Werkzeug mit gezahntem Blatt zum Zerteilen von Holz oder Metall."),
        ("Wasserwaage", "Messgerät mit Luftblase, das zeigt, ob eine Fläche waagerecht ist."),
        ("Maßband", "Aufrollbares Band zum Messen von Längen."),
        ("Schraubenschlüssel", "Werkzeug zum Anziehen und Lösen von Muttern und Bolzen."),
    ],
    "Elektronik": [
        ("Laptop", "Tragbarer Computer mit Bildschirm und Tastatur für Arbeit und Studium."),
        ("Smartphone", "Mobiltelefon mit Touchscreen, Kamera und Internetzugang."),
        ("Kopfhörer", "Paar Lautsprecher fürs Ohr, mit dem man Musik und Podcasts hört."),
        ("Fernseher", "Großer Bildschirm im Wohnzimmer für Filme und Nachrichten."),
        ("Spielkonsole", "Gerät zum Spielen von Videospielen am Fernseher."),
        ("Drucker", "Gerät, das Dokumente und Fotos auf Papier ausgibt."),
        ("Router", "Netzwerkgerät, das Computer und Handys mit dem Internet und dem WLAN verbindet."),
        ("Smartwatch", "Armbanduhr, die Schritte zählt und Nachrichten vom Handy anzeigt."),
    ],
    "Tiere": [
        ("Hund", "Treues Haustier, das bellt, Gassi geht und Stöckchen apportiert."),
        ("Katze", "Selbstständiges Haustier, das schnurrt, Mäuse jagt und gerne schläft."),
        ("Elefant", "Größtes Landtier mit Rüssel und Stoßzähnen, lebt in Afrika und Asien."),
        ("Adler", "Großer Greifvogel mit scharfen Augen, der hoch am Himmel kreist."),
        ("Delfin", "Intelligentes Meeressäugetier, das springt und mit Klicklauten kommuniziert."),
        ("Pferd", "Kräftiges Reittier, das galoppiert und auf der Weide grast."),
        ("Biene", "Fleißiges Insekt, das Nektar sammelt, Blüten bestäubt und Honig produziert."),
        ("Pinguin", "Flugunfähiger Vogel, der in der Antarktis lebt und hervorragend schwimmt."),
    ],
    "Fahrzeuge": [
        ("Auto", "Vierrädriges Fahrzeug mit Motor für Personen auf der Straße."),
        ("Fahrrad", "Zweirad, das mit Muskelkraft über Pedale angetrieben wird."),
        ("Zug", "Schienenfahrzeug, das viele Fahrgäste zwischen Städten transportiert."),
        ("Flugzeug", "Fahrzeug mit Tragflächen, das Passagiere durch die Luft über große Strecken befördert."),
        ("Segelboot", "Wasserfahrzeug, das mit Wind in den Segeln über den See fährt."),
        ("Lastwagen", "Schweres Fahrzeug zum Transport von Waren über die Autobahn."),
        ("Straßenbahn", "Elektrisches Verkehrsmittel auf Schienen im Stadtverkehr."),
        ("Motorrad", "Zweirädriges Kraftfahrzeug mit Motor, bei dem man auf dem Sattel sitzt."),
    ],
    "Musikinstrumente": [
        ("Gitarre", "Saiteninstrument mit sechs Saiten, das gezupft oder geschlagen wird."),
        ("Klavier", "Tasteninstrument mit Hämmerchen und Saiten, gespielt mit zehn Fingern."),
        ("Geige", "Kleines Streichinstrument, das mit einem Bogen gespielt wird."),
        ("Schlagzeug", "Set aus Trommeln und Becken, das mit Stöcken gespielt wird und den Rhythmus vorgibt."),
        ("Querflöte", "Blasinstrument aus Metall, in das man seitlich hineinbläst."),
        ("Trompete", "Blechblasinstrument mit drei Ventilen und hellem, lautem Klang."),
        ("Saxophon", "Blasinstrument mit Mundstück und Klappen, typisch im Jazz."),
        ("Cello", "Großes Streichinstrument, das zwischen den Knien gespielt wird und tief klingt."),
    ],
}

# Absichtlich mehrdeutige Grenzfälle: landen im Vektorraum zwischen den Clustern.
GRENZFAELLE = [
    ("Tomate", "Rote saftige Frucht, die botanisch Obst ist, aber im Salat wie Gemüse verwendet wird."),
    ("Kürbis", "Große orangefarbene Frucht, die als Gemüse gekocht oder zur Suppe verarbeitet wird."),
    ("Küchenhilfe", "Arbeitet in der Gastronomie, schneidet Gemüse und spült Geschirr."),
    ("Bauer", "Baut Kartoffeln, Äpfel und Karotten an und hält Tiere auf dem Hof."),
    ("Hobel", "Werkzeug des Schreiners, mit dem Holz glatt abgetragen wird."),
    ("Hocker", "Einfaches Sitzmöbel ohne Lehne, das auch als kleiner Tisch dient."),
    ("Tierärztin", "Behandelt kranke Hunde, Katzen und Pferde in der Praxis."),
    ("Musiklehrer", "Unterrichtet Schüler in Gitarre, Klavier und Notenlehre."),
]

# Beispielanfragen für die Live-Demo (semantische Suche, ohne Wortüberschneidung)
DEMO_SUCHANFRAGEN = [
    "Wer bringt Kindern etwas bei?",
    "Etwas Süßes zum Naschen aus dem Garten",
    "Worauf kann ich mich zum Fernsehen setzen?",
    "Ich möchte ein Brett zuschneiden",
    "Jemand, der im Notfall hilft",
    "Womit komme ich schnell von A nach B?",
    "Etwas, das Musik macht",
]


def alle_eintraege():
    """Liefert (name, beschreibung, cluster) für alle Datensätze inkl. Grenzfälle."""
    for cluster, items in DEMO_DATEN.items():
        for name, beschreibung in items:
            yield name, beschreibung, cluster
    for name, beschreibung in GRENZFAELLE:
        yield name, beschreibung, "Grenzfall"


if __name__ == "__main__":
    eintraege = list(alle_eintraege())
    print(f"{len(eintraege)} Datensätze in {len(DEMO_DATEN) + 1} Gruppen")