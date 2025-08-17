# Tradelog DataLoader - Anleitung

## Übersicht

Der erweiterte DataLoader ermöglicht es Ihnen, SQLite-Tradelogdateien einfach zu laden und zu verarbeiten. Er erkennt automatisch die Tabellenstruktur und formatiert die Daten in ein einheitliches Format.

## Neue Funktionen

### 1. `load_tradelog_sqlite(db_path, table_name=None)`
- Lädt Tradelog-Daten aus einer SQLite-Datenbank
- Erkennt automatisch die richtige Tabelle (falls mehrere vorhanden)
- Formatiert die Daten automatisch

### 2. `get_sqlite_table_info(db_path)`
- Analysiert die Struktur der SQLite-Datenbank
- Zeigt alle verfügbaren Tabellen und deren Spalten
- Gibt Beispieldaten zurück

### 3. `_format_tradelog_data(data)`
- Standardisiert Spaltennamen
- Konvertiert Datums- und numerische Spalten
- Behandelt fehlende Werte
- Entfernt Duplikate

## Verwendung

### Schritt 1: Pfad anpassen
Öffnen Sie `example_tradelog_loader.py` und passen Sie den Pfad zu Ihrer SQLite-Datei an:

```python
tradelog_db_path = "C:/Users/IhrName/Path/To/Your/tradelog.db"
```

### Schritt 2: Skript ausführen
```bash
python example_tradelog_loader.py
```

### Schritt 3: Ergebnisse prüfen
Das Skript erstellt:
- `output/tradelog_data.csv` - CSV-Export
- `output/tradelog_data.xlsx` - Excel-Export
- Detaillierte Konsolenausgabe mit Datenbankstruktur

## Konfiguration

Die Datei `config/tradelog_config.ini` enthält spezielle Einstellungen für Tradelog-Daten:

```ini
[tradelog]
database_path = data/tradelog.db
default_table = 
date_format = %Y-%m-%d %H:%M:%S

[data_processing]
fill_numeric_na = 0
fill_text_na = Unbekannt
remove_duplicates = true
set_date_index = true
```

## Automatische Erkennung

Der DataLoader erkennt automatisch:

- **Datumsspalten**: Enthalten Wörter wie "date", "datum", "time", "zeit", "timestamp"
- **Numerische Spalten**: Enthalten Wörter wie "price", "preis", "amount", "betrag", "quantity", "menge"
- **Haupttabelle**: Wählt die Tabelle mit den meisten Zeilen aus

## Datenformatierung

Die geladenen Daten werden automatisch:

1. **Spaltennamen standardisiert** (kleinbuchstaben, Unterstriche)
2. **Datumsformat konvertiert** (pandas datetime)
3. **Numerische Werte konvertiert** (float/int)
4. **Index auf Datum gesetzt** (falls verfügbar)
5. **Duplikate entfernt**
6. **Fehlende Werte behandelt**

## Beispiel-Ausgabe

```
=== DATENBANKSTRUKTUR ===
Datenbank: C:/Path/To/tradelog.db
Anzahl Tabellen: 1

Tabelle: trades
  Zeilen: 1250
  Spalten: 8
  Spaltenstruktur:
    - date: TEXT
    - symbol: TEXT
    - type: TEXT
    - quantity: INTEGER
    - price: REAL
    - commission: REAL
    - notes: TEXT
    - timestamp: TEXT

=== GELADENE DATEN ===
Anzahl Zeilen: 1250
Anzahl Spalten: 8
Spalten: ['date', 'symbol', 'type', 'quantity', 'price', 'commission', 'notes', 'timestamp']
```

## Fehlerbehebung

### Häufige Probleme:

1. **Datei nicht gefunden**: Überprüfen Sie den Pfad in `tradelog_db_path`
2. **Keine Tabellen**: Stellen Sie sicher, dass es sich um eine gültige SQLite-Datei handelt
3. **Berechtigungen**: Stellen Sie sicher, dass Sie Lesezugriff auf die Datei haben

### Logs prüfen:
Alle Aktivitäten werden in `logs/tradelog_loader.log` protokolliert.

## Erweiterte Verwendung

### Spezifische Tabelle laden:
```python
# Bestimmte Tabelle laden
data = data_loader.load_tradelog_sqlite(db_path, table_name="specific_table")
```

### Nur Datenbankstruktur analysieren:
```python
# Nur Struktur analysieren, keine Daten laden
db_info = data_loader.get_sqlite_table_info(db_path)
```

### Daten in verschiedenen Formaten speichern:
```python
# Als Parquet speichern
data_loader.save_data(data, "output/data.parquet", "parquet")
```

## Nächste Schritte

Nach dem erfolgreichen Laden der Daten können Sie:

1. **Analyse durchführen**: Verwenden Sie den `TradeAnalyzer`
2. **Visualisierungen erstellen**: Nutzen Sie den `ChartGenerator`
3. **Daten exportieren**: Speichern Sie in verschiedenen Formaten
4. **Weitere Verarbeitung**: Integrieren Sie die Daten in Ihr Trading-System

## Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Logs in `logs/tradelog_loader.log`
2. Stellen Sie sicher, dass alle Abhängigkeiten installiert sind
3. Überprüfen Sie die SQLite-Datei mit einem SQLite-Browser
