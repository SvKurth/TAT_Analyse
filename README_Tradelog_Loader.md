# Tradelog DataLoader - Anleitung

## Übersicht

Der erweiterte DataLoader ermöglicht es Ihnen, SQLite-Tradelogdateien einfach zu laden und zu verarbeiten. Er erkennt automatisch die Tabellenstruktur und formatiert die Daten in ein einheitliches Format. Der DataLoader ist vollständig in das neue Dashboard integriert.

## 🆕 Neue Funktionen

### 1. **Automatische Spaltenerkennung**
- **Datumsspalten**: Erkennt automatisch Spalten wie "DateOpened", "DateClosed", "date", "datum", "time", "zeit", "timestamp"
- **Numerische Spalten**: Erkennt automatisch Spalten wie "price", "preis", "amount", "betrag", "quantity", "menge", "profit", "pnl", "gewinn"
- **Trading-spezifische Spalten**: Erkennt automatisch "type", "typ", "strategy", "strategie"

### 2. **Intelligente Tabellenerkennung**
- **Trade-Tabelle Priorität**: Wählt automatisch die "Trade" oder "trade" Tabelle aus
- **Fallback-Mechanismus**: Falls keine Trade-Tabelle gefunden wird, werden alle verfügbaren Tabellen angezeigt
- **Strukturelle Analyse**: Zeigt detaillierte Informationen über alle Tabellen und deren Spalten

### 3. **Automatische Datenformatierung**
- **Spaltennamen standardisiert** (kleinbuchstaben, Unterstriche)
- **Datumsformat konvertiert** (pandas datetime)
- **Numerische Werte konvertiert** (float/int)
- **Index auf Datum gesetzt** (falls verfügbar)
- **Duplikate entfernt**
- **Fehlende Werte behandelt**

### 4. **.NET-Timestamp Konvertierung**
- **Automatische Konvertierung** von .NET-Timestamps zu lesbaren Datumsformaten
- **DateOpened/DateClosed**: Spezielle Behandlung von Trading-spezifischen Datumsspalten
- **Fallback-Datumskonvertierung** bei Problemen

## 🚀 Verwendung

### **Über das Dashboard (Empfohlen)**
```bash
# 1. Dashboard starten
streamlit run tradelog_dashboard.py

# 2. SQLite-Datei hochladen oder Pfad eingeben
# 3. Automatische Erkennung und Verarbeitung
```

### **Programmatische Verwendung**
```python
from app.services.data_processing_service import DataProcessingService
from app.services.database_service import DatabaseService

# DataLoader initialisieren
data_service = DataProcessingService()
db_service = DatabaseService()

# Datenbank laden
db_path = "path/to/your/tradelog.db"
trade_data = data_service.load_trade_table(db_path)

# Datenbankstruktur analysieren
db_info = db_service.get_database_info(db_path)
```

## 📊 Dashboard-Integration

Der DataLoader ist vollständig in das neue Dashboard integriert und bietet folgende Funktionen:

### **📋 Übersicht-Seite**
- Automatische Erkennung der Datenbankstruktur
- Primärschlüssel-Identifikation
- Optimierte Spaltenreihenfolge

### **📈 Trade-Tabelle-Seite**
- Vollständige Übersicht aller Trade-Daten
- Intelligente Filter und Sortierung
- Paginierung für große Datensätze
- Export in verschiedenen Formaten

### **📊 Trade-Metriken-Seite**
- Umfassende Trading-Statistiken
- Intelligente Spaltenerkennung
- Datums- und Strategie-Filter
- Export gefilterter Daten

### **📅 Kalender-Seite**
- Tagesweise Gewinnübersicht
- Monatsnavigation
- Wochensummen
- Monatsstatistiken

## ⚙️ Konfiguration

Das Dashboard verwendet eine moderne YAML-basierte Konfiguration:

```yaml
# config/default.yaml
database:
  default_path: "data/"
  supported_extensions: [".db", ".db3", ".sqlite", ".sqlite3"]

data_processing:
  auto_detect_columns: true
  convert_dates: true
  handle_missing_values: true
  remove_duplicates: true

trading:
  auto_detect_trade_table: true
  priority_tables: ["Trade", "trade", "Trades", "trades"]
  date_columns: ["DateOpened", "DateClosed", "date", "datum"]
  profit_columns: ["Profit", "profit", "PnL", "pnl", "Gewinn", "gewinn"]
```

## 🔍 Automatische Erkennung

Der DataLoader erkennt automatisch:

### **Trading-spezifische Spalten:**
- **Datumsspalten**: Enthalten Wörter wie "date", "datum", "time", "zeit", "timestamp", "opened", "closed"
- **Numerische Spalten**: Enthalten Wörter wie "price", "preis", "amount", "betrag", "quantity", "menge", "profit", "pnl", "gewinn"
- **Trading-Spalten**: Enthalten Wörter wie "type", "typ", "strategy", "strategie", "symbol", "instrument"

### **Haupttabelle:**
- **Priorität**: "Trade" oder "trade" Tabellen werden bevorzugt
- **Fallback**: Falls keine Trade-Tabelle gefunden wird, werden alle verfügbaren Tabellen angezeigt
- **Intelligente Auswahl**: Wählt die Tabelle mit den meisten relevanten Spalten aus

## 📊 Beispiel-Ausgabe

```
=== DATENBANKSTRUKTUR ===
Datenbank: C:/Path/To/tradelog.db
Anzahl Tabellen: 1

Tabelle: Trade
  Zeilen: 1250
  Spalten: 8
  Primärschlüssel: id
  Spaltenstruktur:
    - id: INTEGER (PRIMARY KEY)
    - DateOpened: TEXT (-> konvertiert zu datetime)
    - DateClosed: TEXT (-> konvertiert zu datetime)
    - Symbol: TEXT
    - Type: TEXT
    - Quantity: INTEGER
    - Price: REAL
    - Profit: REAL

=== GELADENE DATEN ===
Anzahl Zeilen: 1250
Anzahl Spalten: 8
Spalten: ['id', 'DateOpened', 'DateClosed', 'Symbol', 'Type', 'Quantity', 'Price', 'Profit']
Datumsspalten erkannt: ['DateOpened', 'DateClosed']
Profit-Spalten erkannt: ['Profit']
```

## 🚨 Fehlerbehebung

### **Häufige Probleme:**

1. **Datei nicht gefunden**
   - Überprüfen Sie den Dateipfad
   - Stellen Sie sicher, dass die Datei existiert

2. **Keine Tabellen gefunden**
   - Stellen Sie sicher, dass es sich um eine gültige SQLite-Datei handelt
   - Überprüfen Sie die Datei mit einem SQLite-Browser

3. **Berechtigungen**
   - Stellen Sie sicher, dass Sie Lesezugriff auf die Datei haben
   - Überprüfen Sie die Windows-Berechtigungen

4. **Datumsspalten werden nicht erkannt**
   - Überprüfen Sie die Spaltennamen
   - Stellen Sie sicher, dass die Spalten Datumsdaten enthalten

### **Logs prüfen:**
Alle Aktivitäten werden in der Streamlit-Konsole protokolliert.

## 🔧 Erweiterte Verwendung

### **Spezifische Tabelle laden:**
```python
# Bestimmte Tabelle laden
data = data_service.load_specific_table(db_path, table_name="specific_table")
```

### **Nur Datenbankstruktur analysieren:**
```python
# Nur Struktur analysieren, keine Daten laden
db_info = db_service.get_database_info(db_path)
```

### **Daten in verschiedenen Formaten speichern:**
```python
# Als CSV speichern
data_service.export_data(data, "output/data.csv", "csv")

# Als Excel speichern
data_service.export_data(data, "output/data.xlsx", "excel")
```

## 📁 Aktuelle Projektstruktur

```
TAT_Analyse/
├── app/                           # Core-Services
│   ├── services/
│   │   ├── data_processing_service.py  # Erweiterter DataLoader
│   │   ├── database_service.py         # Datenbankoperationen
│   │   └── trade_data_service.py       # Trading-spezifische Funktionen
│   └── core/
│       ├── config_service.py           # Konfigurationsverwaltung
│       └── logging_service.py          # Logging
├── modules/                        # Dashboard-Seiten
│   ├── overview_page.py              # Übersicht
│   ├── data_analysis_page.py         # Datenanalyse
│   ├── visualization_page.py         # Visualisierungen
│   ├── export_page.py                # Export
│   ├── settings_page.py              # Einstellungen
│   ├── trade_table_page.py           # Trade-Tabelle
│   ├── metrics_page.py               # Trade-Metriken
│   └── calendar_page.py              # Kalender
├── config/                          # Konfigurationsdateien
│   └── default.yaml                 # Hauptkonfiguration
├── tradelog_dashboard.py            # Hauptdashboard
├── requirements.txt                 # Abhängigkeiten
└── README.md                        # Hauptdokumentation
```

## 🎯 Nächste Schritte

Nach dem erfolgreichen Laden der Daten können Sie:

1. **Dashboard verwenden**: Nutzen Sie alle 7 Hauptseiten für umfassende Analysen
2. **Trade-Daten analysieren**: Verwenden Sie die spezialisierten Trading-Seiten
3. **Daten exportieren**: Speichern Sie in verschiedenen Formaten
4. **Weitere Verarbeitung**: Integrieren Sie die Daten in Ihr Trading-System

## 🔗 Integration

Der DataLoader ist vollständig in das Dashboard integriert und kann:

- **Automatisch** beim Hochladen von SQLite-Dateien verwendet werden
- **Programmatisch** über die Service-Klassen aufgerufen werden
- **Erweitert** werden für spezifische Anforderungen

## 📞 Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Streamlit-Konsole auf Fehlermeldungen
2. Stellen Sie sicher, dass alle Abhängigkeiten installiert sind
3. Überprüfen Sie die SQLite-Datei mit einem SQLite-Browser
4. Siehe auch: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Viel Erfolg bei der Analyse Ihrer Trading-Daten! 🎯📊**
