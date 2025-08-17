# 📊 Tradelog Dashboard - Interaktive Oberfläche

## Übersicht

Das Tradelog Dashboard ist eine interaktive Web-Anwendung, die es Ihnen ermöglicht, SQLite-Tradelogdateien direkt im Browser anzuschauen, zu analysieren und zu migrieren. Es bietet eine benutzerfreundliche Oberfläche mit verschiedenen Funktionen zur Datenexploration.

## 🚀 Features

### 📋 Übersicht
- **Datenbankstruktur**: Zeigt alle Tabellen und deren Spalten
- **Metriken**: Anzahl Zeilen, Spalten, Tabellen auf einen Blick
- **Datenvorschau**: Interaktive Tabellen mit anpassbarer Zeilenanzahl
- **Spaltenfilter**: Wählen Sie aus, welche Spalten angezeigt werden sollen

### 📊 Datenanalyse
- **Statistiken**: Detaillierte Beschreibung numerischer Spalten
- **Kategorische Daten**: Analyse eindeutiger Werte und Verteilungen
- **Fehlende Werte**: Visualisierung und Quantifizierung fehlender Daten
- **Duplikate**: Erkennung und Anzeige doppelter Einträge

### 📈 Visualisierungen
- **Histogramme**: Verteilungen numerischer Spalten
- **Boxplots**: Ausreißer und Verteilungen identifizieren
- **Zeitreihen**: Daten über Zeit visualisieren (falls Datumsspalten vorhanden)
- **Korrelationsmatrix**: Zusammenhänge zwischen numerischen Spalten
- **Verteilungsplots**: Mehrere Spalten gleichzeitig analysieren

### 💾 Export & Migration
- **Mehrere Formate**: CSV, Excel, Parquet, JSON
- **Spaltenauswahl**: Wählen Sie aus, welche Daten exportiert werden sollen
- **Batch-Export**: Alle Formate gleichzeitig exportieren
- **Download-Funktion**: Direkter Download der exportierten Dateien

### 🔧 Einstellungen
- **Datenbankdetails**: Pfad, Größe, Erstellungsdatum
- **Datenqualität**: Score basierend auf fehlenden Werten
- **Datentypen**: Übersicht über alle Spaltentypen
- **Speicherverbrauch**: Analyse des Speicherverbrauchs pro Spalte

## 🛠️ Installation

### 1. Abhängigkeiten installieren
```bash
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
- **Übersicht**: Schauen Sie sich die Struktur Ihrer Daten an
- **Analyse**: Untersuchen Sie Statistiken und Datenqualität
- **Visualisierungen**: Erstellen Sie Charts für besseres Verständnis

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

## ⚙️ Konfiguration

Das Dashboard verwendet die gleiche Konfiguration wie der DataLoader:
- `config/config.ini` - Hauptkonfiguration
- `config/tradelog_config.ini` - Tradelog-spezifische Einstellungen

## 🎨 Anpassung

### CSS-Styling
Das Dashboard verwendet benutzerdefiniertes CSS für ein modernes Design. Sie können das Styling in der `main()`-Funktion anpassen.

### Neue Chart-Typen
Fügen Sie neue Visualisierungen in der `show_visualization_tab()`-Funktion hinzu.

### Zusätzliche Export-Formate
Erweitern Sie die Export-Funktionalität in der `show_export_tab()`-Funktion.

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
- **Batch-Verarbeitung**: Kombinieren Sie mit dem `example_tradelog_loader.py`

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

---

**Viel Spaß beim Erkunden Ihrer Tradelog-Daten! 🎯📊**
