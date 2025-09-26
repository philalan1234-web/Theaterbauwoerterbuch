#BESCHREIBUNG
Dieses Python-Skript dient der automatisierten Digitalisierung von handgeschriebenen Karteikarten für das Projekt "Theaterbauwörterbuch".
Das zugrundeliegende Wörterbuch aus der DDR-Zeit erhielt die SLUB vor zwei Jahren von Dr. Eßmann, einem ehemaligen Mitarbeiter des Instituts für Kulturbauten. Hierfür wird die Google Gemini API verwendet, um Text aus Bilddateien (OCR) zu erkennen und die gewonnenen Informationen in ein vordefiniertes, strukturiertes JSON-Format zu überführen.

#ZIEL
Ein analoger Zettelkasten in eine suabere, maschinenlesbare und durchsuchbare digitale Datensammlungen zu transformieren.

#FEATURES
- Verarbeitet automatisch ganze Ordner voller Bilddateien
- Erzwingt durch das Pydantic-Schema eine exakte und konsistente JSON-Struktur für jede extrahierte Karteikarte
- Vergibt automatisch einzigartige, fortlaufende IDs, selbst bei einem Neustart.
- Verarbeitet Bilddateien in alphabetischer Reihenfolge
- Sammelt KI gemeldete "Bemerkungen" und gibt am Ende einen Bericht im Terminal aus
- Die finalen JSON-Dateien erhalten nur reine und saubere Daten

#VORRAUSSETZUNGEN
folgende Softwares müssen auf Ihrem System installiert sein:
- Anaconda
- Python 3.11
- Google AI API-Schlüssel

#INSTALLATION & EINRICHTUNG
1. Skript-Datei in einen Projektordner auf Ihren Computer Laden.
2. Erstellen Sie eine isolierte Umgebung, um Konflikte mit anderen Python-Projekten zu vermeiden: 
conda create --name HIER IHREN PROJEKTNAMEN EINGEBEN python=3.11
3. Wechseln Sie in die neu erstellte Umgebung:
conda activate HIER IHREN PROJEKTNAMEN EINGEBEN
4. Installieren Sie alle notwendigen Python-Pakete:
pip install google-generativeai pydantic rich

#KONFIGURATIONEN
Öffnen Sie die Python-Skriptdatei (.py) in einem Textiditor und passen Sie die folgenden 3 Variablen am Anfag des Hauptprogramms an:
if __name__ == "__main__":
GOOGLE_API_KEY = "HIER IHREN API-KEY EINGEBEN"
IMAGE_SOURCE_FOLDER = r"C:\pfad\zu\ihren\bildern"
OUTPUT_JSON_FILE = r"C:\pfad\zur\ausgabedatei\ergebnis.json"

#ANWENDUNGEN
Führen Sie das Skript über den Anaconda Prompt aus:
1. In den Projektordner navigieren:
cd PFAD\ZUM\PROJEKTORDNER
2. Das Skript starten:
python IHR_SKRIPTNAME.py

#OUTPUT
Diese 2 Ergebnisse werden ausgegeben:
1. Terminal-Bericht: Eine Live-Anzeige des Fortschritts und eine finale Zusammenfassungen, der Anzahl der neu hinzugefügten Karten, sowie eine Liste aller gefundenen "Bemerkungen" enthält.
2. JSON-Datei: Eine einzelne saubere .json-Datei am vordefinierten Speicherort. Diese Datei enthält die vollständige Sammlung aller extrahierten Karteikarten und wird bei jedem Programmlauf aktualisiert.

#AUTOREN
Phil Seidel - Projektentwickler
Kay-Michael Würzner - Projektleiter