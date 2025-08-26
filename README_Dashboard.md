# 📊 Tradelog Dashboard - Interaktive Oberfläche

## Übersicht

Das Tradelog Dashboard ist eine interaktive Web-Anwendung, die es Ihnen ermöglicht, SQLite-Tradelogdateien direkt im Browser anzuschauen, zu analysieren und zu migrieren. Es bietet eine benutzerfreundliche Oberfläche mit verschiedenen Funktionen zur Datenexploration.

## 🚀 Features

### 🧭 **Neue Seitenstruktur (keine Tabs mehr)**
Das Dashboard verwendet jetzt eine moderne Seitenstruktur mit 7 Hauptseiten, die über die linke Sidebar ausgewählt werden können:

### 📋 **📋 Übersicht**
- **Datenbankstruktur**: Zeigt alle Tabellen und deren Spalten
- **Metriken**: Anzahl Zeilen, Spalten, Tabellen auf einen Blick
- **Datenvorschau**: Interaktive Tabellen mit anpassbarer Zeilenanzahl
- **Spaltenfilter**: Wählen Sie aus, welche Spalten angezeigt werden sollen
- **Primärschlüssel-Identifikation**: Automatische Erkennung und Anzeige der Primärschlüssel-Spalten

### 📊 **📊 Datenanalyse**
- **Statistiken**: Detaillierte Beschreibung numerischer Spalten
- **Kategorische Daten**: Analyse eindeutiger Werte und Verteilungen
- **Fehlende Werte**: Visualisierung und Quantifizierung fehlender Daten
- **Duplikate**: Erkennung und Anzeige doppelter Einträge

### 📈 **📈 Visualisierungen**
- **Histogramme**: Verteilungen numerischer Spalten
- **Boxplots**: Ausreißer und Verteilungen identifizieren
- **Zeitreihen**: Daten über Zeit visualisieren (falls Datumsspalten vorhanden)
- **Korrelationsmatrix**: Zusammenhänge zwischen numerischen Spalten
- **Verteilungsplots**: Mehrere Spalten gleichzeitig analysieren

### 💾 **💾 Export & Migration**
- **Mehrere Formate**: CSV, Excel, Parquet, JSON
- **Spaltenauswahl**: Wählen Sie aus, welche Daten exportiert werden sollen
- **Batch-Export**: Alle Formate gleichzeitig exportieren
- **Download-Funktion**: Direkter Download der exportierten Dateien

### 🔧 **🔧 Einstellungen**
- **Datenbankdetails**: Pfad, Größe, Erstellungsdatum
- **Datenqualität**: Score basierend auf fehlenden Werten
- **Datentypen**: Übersicht über alle Spaltentypen
- **Speicherverbrauch**: Analyse des Speicherverbrauchs pro Spalte

### 📈 **📈 Trade-Tabelle**
- **Vollständige Übersicht**: Alle Trade-Daten in einer übersichtlichen Tabelle
- **Intelligente Filter**: Nach Spalten, Datum und Werten filtern
- **Sortierung**: Nach beliebigen Spalten sortieren (aufsteigend/absteigend)
- **Paginierung**: Große Datensätze seitenweise durchblättern
- **Spaltenauswahl**: Nur relevante Spalten anzeigen
- **Export**: Gefilterte Daten in verschiedenen Formaten exportieren
- **Primärschlüssel-Identifikation**: Automatische Erkennung und Anzeige der Primärschlüssel-Spalten

### 📊 **📊 Trade-Metriken**
- **Kachelbasierte Darstellung** wichtiger Trading-Statistiken
- **🔍 Umfassende Filter-Funktionen**:
  - **📅 Datumsfilter**: Immer DateOpened Spalte (automatische Erkennung)
  - **🎯 Trade Type Filter**: Nach spezifischen Trade Types filtern
  - **🎯 Strategy Filter**: Nach verwendeten Strategies filtern
- **Intelligente Spaltenerkennung** (Profit, Preis, DateOpened, Trade Type, Strategy, etc.)
- **Umfassende Trading-Statistiken** (Gewinnrate, Durchschnittsprofit, etc.)
- **Zeitbasierte Metriken** (Trading-Tage, Trades pro Tag) basierend auf DateOpened und gefilterten Daten
- **Datenqualitätsbewertung** für gefilterte Daten
- **💾 Export gefilterter Daten** als CSV
- **Filter-Zusammenfassung** mit Effekt-Anzeige

### 📅 **📅 Kalender**
- **Tagesgewinn pro Tag**: Übersichtliche Kalenderansicht
- **Monatsnavigation**: Einfache Navigation zwischen Monaten
- **Wochensummen**: Automatische Berechnung der Wochengewinne
- **Monatsstatistiken**: Positive/negative Tage, Durchschnittswerte
- **Strategie-Filter**: Nach spezifischen Trading-Strategien filtern
- **Wöchentliche Zusammenfassung**: Samstags-Zusammenfassungen

## 🛠️ Installation

### 1. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
pip install -r requirements_dashboard.txt
```

### 2. Dashboard starten
```bash
streamlit run tradelog_dashboard.py
```

Das Dashboard öffnet sich automatisch in Ihrem Standard-Webbrowser.

## 📖 Verwendung

### Schritt 1: Daten laden
- **Datei hochladen**: Verwenden Sie den Upload-Button in der Seitenleiste
- **Pfad eingeben**: Oder geben Sie den vollständigen Pfad zu Ihrer SQLite-Datei ein

### Schritt 2: Daten erkunden
- **Seitenauswahl**: Wählen Sie die gewünschte Seite aus der linken Sidebar
- **Übersicht**: Schauen Sie sich die Struktur Ihrer Daten an
- **Analyse**: Untersuchen Sie Statistiken und Datenqualität
- **Visualisierungen**: Erstellen Sie Charts für besseres Verständnis
- **Trade-Tabelle**: Vollständige Übersicht aller Trading-Daten
- **Trade-Metriken**: Detaillierte Trading-Statistiken
- **Kalender**: Tagesweise Gewinnübersicht

### Schritt 3: Daten exportieren
- **Format wählen**: Wählen Sie das gewünschte Export-Format
- **Spalten auswählen**: Bestimmen Sie, welche Daten exportiert werden sollen
- **Export starten**: Laden Sie die Datei herunter oder speichern Sie sie lokal

## 🎯 Anwendungsfälle

### 🔍 Datenexploration
- Schnelle Übersicht über neue Tradelogdateien
- Identifikation von Datenqualitätsproblemen
- Verständnis der Datenstruktur

### 📊 Reporting
- Erstellung von Visualisierungen für Präsentationen
- Export von Daten für weitere Analysen
- Generierung von Berichten in verschiedenen Formaten

### 🔄 Datenmigration
- Konvertierung zwischen verschiedenen Formaten
- Vorbereitung von Daten für andere Systeme
- Backup und Archivierung von Tradelogdaten

### 🧹 Datenqualität
- Erkennung fehlender Werte
- Identifikation von Duplikaten
- Überprüfung der Datenkonsistenz

### 📈 Trading-Analyse
- Tagesweise Gewinnübersicht
- Strategie-Performance-Analyse
- Trading-Metriken und Statistiken

## ⚙️ Konfiguration

Das Dashboard verwendet die gleiche Konfiguration wie der DataLoader:
- `config/default.yaml` - Hauptkonfiguration
- Automatische Erkennung von Trading-spezifischen Spalten

## 🎨 Anpassung

### CSS-Styling
Das Dashboard verwendet benutzerdefiniertes CSS für ein modernes Design. Sie können das Styling in den jeweiligen Modulen anpassen.

### Neue Seiten hinzufügen
Fügen Sie neue Seiten in das `modules/` Verzeichnis hinzu und registrieren Sie sie in der Hauptnavigation.

### Zusätzliche Export-Formate
Erweitern Sie die Export-Funktionalität in den jeweiligen Modulen.

## 🚨 Fehlerbehebung

### Häufige Probleme:

1. **Streamlit startet nicht**
   - Überprüfen Sie, ob alle Abhängigkeiten installiert sind
   - Stellen Sie sicher, dass Python 3.8+ verwendet wird

2. **Datei kann nicht geladen werden**
   - Überprüfen Sie den Dateipfad
   - Stellen Sie sicher, dass es sich um eine gültige SQLite-Datei handelt

3. **Charts werden nicht angezeigt**
   - Überprüfen Sie, ob Plotly korrekt installiert ist
   - Stellen Sie sicher, dass die Daten die richtigen Datentypen haben

4. **Export funktioniert nicht**
   - Überprüfen Sie die Schreibberechtigungen im Ausgabeverzeichnis
   - Stellen Sie sicher, dass genügend Speicherplatz verfügbar ist

### Logs prüfen:
Alle Aktivitäten werden in der Streamlit-Konsole protokolliert.

## 🔗 Integration

Das Dashboard kann einfach in bestehende Workflows integriert werden:

- **Automatisierung**: Starten Sie das Dashboard über Skripte
- **API-Integration**: Verwenden Sie die DataLoader-Funktionen direkt
- **Batch-Verarbeitung**: Kombinieren Sie mit den Modulen

## 📱 Browser-Kompatibilität

Das Dashboard funktioniert optimal mit:
- Chrome/Chromium (empfohlen)
- Firefox
- Safari
- Edge

## 🚀 Performance-Tipps

- **Große Dateien**: Für sehr große Datenbanken (>100MB) kann das Laden länger dauern
- **Spaltenfilter**: Verwenden Sie Spaltenfilter, um nur relevante Daten anzuzeigen
- **Zeilenanzahl**: Begrenzen Sie die angezeigten Zeilen für bessere Performance

## 🔮 Zukünftige Features

Geplante Erweiterungen:
- **Datenbankverbindungen**: Direkte Verbindung zu laufenden Datenbanken
- **Echtzeit-Updates**: Automatische Aktualisierung bei Datenänderungen
- **Erweiterte Charts**: Candlestick-Charts für Trading-Daten
- **Datenbank-Editor**: Direkte Bearbeitung von Daten im Dashboard
- **Benutzerverwaltung**: Multi-User-Support mit Berechtigungen

## 📞 Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Streamlit-Konsole auf Fehlermeldungen
2. Stellen Sie sicher, dass alle Abhängigkeiten installiert sind
3. Testen Sie mit einer einfachen SQLite-Datei
4. Überprüfen Sie die Browser-Konsole auf JavaScript-Fehler
5. Siehe auch: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Viel Spaß beim Erkunden Ihrer Tradelog-Daten! 🎯📊**
