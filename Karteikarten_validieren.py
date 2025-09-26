#---Download von Bibliotheken---
import json #Vorraussetzung für pydantic
import time #Pausen zwischen Antworten
from enum import Enum #Aufzählungen
from pathlib import Path #Dateipfade benutzen
from typing import Optional, Literal, List, Dict, Any #Definition von Dateitypen
from pydantic import BaseModel, Field #Datenstrukturierung
from rich import print #aussehen von Terminal-Ausgaben

#---Download-Versuch der Google GenAI-Bibliothek---
try:
    import google.generativeai as genai
    from google.generativeai.types import FunctionDeclaration, Tool
except ImportError:
    print("Google GenAI ist nicht installiert. Bitte installieren Sie es mit: pip install google-generativeai")
    exit()
#---Anpassen des erzeugten Schemas an Google-API ($defs)---
def flatten_pydantic_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    if "$defs" in schema:
        defs = schema.pop("$defs")
        def resolve_refs(obj):
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref_key = obj["$ref"].split('/')[-1]
                    return resolve_refs(defs.get(ref_key, {}))
                else:
                    return {k: resolve_refs(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [resolve_refs(item) for item in obj]
            else:
                return obj
        return resolve_refs(schema)
    return schema
#---Anpassen des erzeugten Schemas an Google-API (title)---
def remove_titles_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    if 'title' in schema:
        del schema['title']
    for key, value in list(schema.items()):
        if isinstance(value, dict):
            remove_titles_from_schema(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    remove_titles_from_schema(item)
    return schema
#---Anpassen des erzeugten Schemas an Google-API (anyOf)---
def simplify_anyof_in_schema(obj: Any) -> Any:
    if isinstance(obj, dict):
        if "anyOf" in obj:
            non_null_schema = next((item for item in obj["anyOf"] if item.get("type") != "null"), None)
            if non_null_schema:
                return simplify_anyof_in_schema(non_null_schema)
        return {k: simplify_anyof_in_schema(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [simplify_anyof_in_schema(i) for i in obj]
    else:
        return obj
#---Definiert Struktur für verschachtelte Übersetzungsobjekt---
class Uebersetzung(BaseModel):
    englisch: Optional[str] = Field(None, description="Die englische Übersetzung.")
    franzoesisch: Optional[str] = Field(None, description="Die französische Übersetzung.")
    tschechisch: Optional[str] = Field(None, description="Die tschechische Übersetzung.")
#---Definiert Struktur für Karteikarte---
class Karteikarte(BaseModel):
    id: str = Field(..., description="Eindeutige, generierte ID der Karteikarte.")
    begriff: str = Field(..., description="Der Hauptbegriff auf der Karte.")
    wortart: Literal[
        "Verben", "Nomen", "Partikeln", "Adjektive", "Pronomen", 
        "Numeralia", "Artikel", "Adverbien", "Präpositionen", "Konjunktionen"
    ] = Field(..., description="Die Wortart des Begriffs.")
    genus: Optional[Literal["m", "f", "n"]] = Field(None, description="Das Genus (m, f, n), falls es sich um ein Nomen handelt.")
    definition: Optional[str] = Field(None, description="Die Definition oder Beschreibung des Begriffs.")
    referenz: Optional[str] = Field(None, description="Ein Verweis, der typischerweise mit '→' beginnt.")
    uebersetzung: Optional[Uebersetzung] = Field(None, description="Die Übersetzungen des Begriffs.")
    bemerkungen: Optional[str] = Field(None, description="Besondere Anmerkungen (z.B. unleserlich, durchgestrichen).")
class KarteikartenSammlung(BaseModel):
    """Eine Sammlung aller auf einem Bild gefundenen Karteikarten."""
    karten: List[Karteikarte]
#---Konfiguration mit eigenen Daten---
if __name__ == "__main__":
    GOOGLE_API_KEY = "AIzaSyCCZmIYNDEu-MAweTH1oTVVwaOv7-a7lsQ"
    IMAGE_SOURCE_FOLDER = r"K:\mein_woerterbuch\Scans\Theaterbau Scans"
    OUTPUT_JSON_FILE = r"K:\mein_woerterbuch\Ergebnisse\extrahierte_karteikarten_V.json"

    final_collection = KarteikartenSammlung(karten=[])
    card_counter = 1
    output_path = Path(OUTPUT_JSON_FILE)

    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"Lade '{output_path.name}'...")
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if 'karten' in existing_data and existing_data['karten']:
                    final_collection = KarteikartenSammlung(karten=existing_data['karten'])
                    highest_id = max(int(card.id.split('-')[0]) for card in final_collection.karten if card.id and '-' in card.id)
                    card_counter = highest_id + 1
            print(f"{len(final_collection.karten)} Karten geladen. ID-Zähler startet bei {card_counter}.")
        except Exception as e:
            print(f"WARNUNG: Bestehende Datei konnte nicht verarbeitet werden. Beginne neu. Fehler: {e}")
            final_collection = KarteikartenSammlung(karten=[])
            card_counter = 1
#---API-Setup---
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")
#---Bereinigt das Schema---
    raw_schema = KarteikartenSammlung.model_json_schema()
    flat_schema = flatten_pydantic_schema(raw_schema)
    no_title_schema = remove_titles_from_schema(flat_schema)
    final_schema = simplify_anyof_in_schema(no_title_schema)
#---Erstellt Datei, die der KI zugeschickt wird---
    karteikarten_tool = Tool(
        function_declarations=[
            FunctionDeclaration(
                name="KarteikartenSammlung",
                description="Extrahiert und sammelt alle gefundenen Karteikarten von einem Bild.",
                parameters=final_schema
            )
        ]
    )
#---verfolgt den Pfad und durchsucht den Ordner und ordet alphabetisch---
    source_path = Path(IMAGE_SOURCE_FOLDER)
    unsorted_images = list(source_path.glob('*.jpg')) + list(source_path.glob('*.jpeg')) + list(source_path.glob('*.png'))
    image_files = sorted(unsorted_images)
#---Fehlermeldung bei keinem Fund---
    if not image_files:
        print(f"Keine Bilddateien im Ordner '{source_path}' gefunden.")
        exit()

    print(f"Verarbeite '{len(image_files)}' Bilder...")
    
    initial_card_count = len(final_collection.karten)
    bemerkungen_gefunden = []
#---Schleife, um jede Datei durchzugehen---    
    for i, image_path in enumerate(image_files, 1):
        print(f"\n--- [{i}/{len(image_files)}] Verarbeite: {image_path.name} ---")
#---Stellt sicher, dass nach Fehlermeldung nicht abgebrochen wird---
        try:
#---Dateiendung auslesen und in Kleinbuchstaben umwandeln---
            extension = image_path.suffix.strip('.').lower()
#---Korrigiere 'jpg' zu 'jpeg' für den MIME-Typ---
            if extension == "jpg":
                mime_type = "image/jpeg"
            else:
                mime_type = f"image/{extension}"

            image_part = {"mime_type": mime_type, "data": image_path.read_bytes()}
#---Prompt für Gemini---
            prompt = prompt = """
            AUFGABE: Du bist ein Assistenzsystem und sollst handgeschriebene deutsche Karteikarten digitalisieren. Die Bilddatei enthält IMMER GENAU 3 Karteikarten. Wandle jede Karte in ein separates JSON-Objekt um und befolge exakt die folgenden Regeln.

            AUFBAU DES JSON-OBJEKTS:
            - Begriff: Der Hauptbegriff aus der ersten Zeile.
            - Wortart: Die Wortart (z.B. "Nomen", "Verben").
            - Genus: Nur wenn Wortart="Nomen". Übernimm den Wert (m, f, n) aus der Klammer.
            - Definition: Eingerückter Text, wenn kein Pfeil (→) davorsteht.
            - Referenz: Eingerückter Text, wenn ein Pfeil (→) davorsteht.
            - Übersetzung: Ein verschachteltes Objekt mit den Feldern "Englisch", "Französisch", "Tschechisch".
            - Bemerkungen: Ein Textfeld für alle besonderen Anmerkungen.

            VORGABEN:
            - Gib exakt den Text der Karten wieder.
            - Nutze das Bemerkungs-Feld für unleserliche Wörter, Fehler auf der Karte oder durchgestrichene Wörter.
            - Achte exakt auf alle Akzente und Umlaute."""
#---Sendet Anfrage an Google-API ud wartet aud Antwort---
            response = model.generate_content(
                contents=[prompt, image_part],
                tools=[karteikarten_tool],
                tool_config={'function_calling_config': {'mode': 'any'}}
            )
#---Wandelt strukturierte Daten in ein sauberes Python-Objekt um---
            function_call = response.candidates[0].content.parts[0].function_call

            if function_call.args and 'karten' in function_call.args:
                karten_von_ki = function_call.args.get('karten', [])
                
                if karten_von_ki:
                    # Schleife NUR für ID-Zuweisung
                    for karte_dict in karten_von_ki:
                        begriff = karte_dict.get('begriff', '')
                        prefix = "".join(c for c in begriff[:4] if c.isalnum()).lower()
                        karte_dict['id'] = f"{card_counter}-{prefix}"
                        card_counter += 1
                    
                    # Validierung und Hinzufügen NACH der Schleife
                    sammlung_from_image = KarteikartenSammlung(karten=karten_von_ki)
                    final_collection.karten.extend(sammlung_from_image.karten)
                    
                    for karte in sammlung_from_image.karten:
                        if karte.bemerkungen:
                            bemerkungen_gefunden.append(f"  - ID {karte.id} ({karte.begriff}): {karte.bemerkungen}")
                    print(f"✅ Erfolg! {len(sammlung_from_image.karten)} Karte(n) hinzugefügt.")
                else:
                    print("⚠️ Keine Karten in diesem Bild gefunden.")

            time.sleep(1)
        except Exception as e:
            print(f"❌ FEHLER bei der Verarbeitung von {image_path.name}: {e}")
            continue
    #---Speichern der Ergebnisse---
    if final_collection.karten:
        added_cards_count = len(final_collection.karten) - initial_card_count

        print(f"\n--- 🏁 Verarbeitung abgeschlossen ---")
        
        if bemerkungen_gefunden:
            print("\n--- ⚠️ Gefundene Bemerkungen ---")
            for b in bemerkungen_gefunden:
                print(b)
            print("---------------------------------")

        if added_cards_count > 0:
            print(f"\n{added_cards_count} neue Karten hinzugefügt.")
        print(f"Insgesamt sind jetzt {len(final_collection.karten)} Karten in der Sammlung.")
        try:
            with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
                # Das 'bemerkungen'-Feld wird beim Speichern ausgeschlossen
                f.write(final_collection.model_dump_json(
                    indent=2,
                    exclude={'karten': {'__all__': {'bemerkungen'}}}
                ))
            print(f"Die komplette Sammlung wurde in '{OUTPUT_JSON_FILE}' gespeichert.")
        except Exception as e:
            print(f"Fehler beim Speichern der finalen JSON-Datei: {e}")
    else:
        print("\n--- 🏁 Verarbeitung abgeschlossen ---")
        print("Es wurden keine Karten aus den Bildern extrahiert.")