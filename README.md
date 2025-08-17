# 📊 Trade Analysis - Tradelog Dashboard

Ein interaktives Dashboard zur Analyse und Migration von SQLite-Tradelogdateien.

## 🚀 Features

### 📋 **Hauptfunktionen**
- **SQLite-Unterstützung**: Lädt `.db`, `.db3`, `.sqlite`, `.sqlite3` Dateien
- **Interaktive Visualisierungen**: Charts und Grafiken mit Plotly
- **Datenanalyse**: Automatische Erkennung von Datums- und numerischen Spalten
- **Export-Funktionen**: CSV, Excel, Parquet, JSON

### 🆕 **Neue Trade-Tabelle-Seite**
- **Vollständige Übersicht**: Alle Trade-Daten in einer übersichtlichen Tabelle
- **Intelligente Filter**: Nach Spalten, Datum und Werten filtern
- **Sortierung**: Nach beliebigen Spalten sortieren (aufsteigend/absteigend)
- **Paginierung**: Große Datensätze seitenweise durchblättern
- **Spaltenauswahl**: Nur relevante Spalten anzeigen
- **Export**: Gefilterte Daten in verschiedenen Formaten exportieren

### 🎯 **Trade-Tabelle-Fokus**
- **Automatische Erkennung**: Das Dashboard sucht spezifisch nach der "Trade"-Tabelle
- **Priorität**: "Trade" oder "trade" Tabellen werden bevorzugt geladen
- **Fallback**: Falls keine Trade-Tabelle gefunden wird, werden alle verfügbaren Tabellen angezeigt
- **Einfache Anzeige**: Komplette Tabelle ohne Filter oder Paginierung
- **🔑 Primärschlüssel-Identifikation**: Automatische Erkennung und Anzeige der Primärschlüssel-Spalten
- **📊 Optimierte Spaltenreihenfolge**: Primärschlüssel werden automatisch als erste Spalten angezeigt

## 🎯 Verwendung

### 1. **Dashboard starten**
```bash
# Virtuelle Umgebung aktivieren
.\venv\Scripts\Activate.ps1

# Dashboard starten
streamlit run tradelog_dashboard.py
```

### 2. **Daten laden**
- **Datei hochladen**: Ziehen Sie Ihre `.db3` Datei in den Upload-Bereich
- **Oder Pfad eingeben**: Geben Sie den vollständigen Pfad zu Ihrer Datei ein

### 3. **Trade-Tabelle analysieren**
- **Tab "📈 Trade-Tabelle"** wählen
- **Spalten auswählen**: Wählen Sie die relevanten Spalten aus
- **Filter anwenden**: Nach Datum, Werten oder Spalten filtern
- **Sortieren**: Nach beliebigen Spalten sortieren
- **Daten exportieren**: Gefilterte Daten in verschiedenen Formaten herunterladen

## 📊 Dashboard-Struktur

### 🧭 **Sidebar-Navigation**
- **Komplette Seitenauswahl**: Wechseln Sie zwischen verschiedenen Hauptseiten über die linke Sidebar
- **Selectbox-Auswahl**: Saubere Dropdown-Auswahl für alle verfügbaren Seiten
- **Keine Tabs mehr**: Jede Seite wird als vollständige, eigenständige Ansicht angezeigt
- **7 Hauptseiten** zur Auswahl

### 📋 **📋 Übersicht**
- Datenbankstruktur und Metriken
- Tabelleninformationen
- Datenvorschau

### 📊 **📊 Datenanalyse**
- Statistische Zusammenfassungen
- Fehlende Werte und Duplikate
- Datenqualitätsmetriken

### 📈 **📈 Visualisierungen**
- Histogramme, Boxplots, Zeitreihen
- Korrelationsmatrizen
- Verteilungsanalysen

### 💾 **💾 Export/Migration**
- Einzelne Formate exportieren
- Batch-Export aller Formate
- Spaltenauswahl für Export

### 🔧 **🔧 Einstellungen**
- Datenbankdetails
- Datenqualitätsbewertung
- Speicherverbrauch

### 📈 **📈 Trade-Tabelle**
- Vollständige Übersicht aller Trade-Daten
- Primärschlüssel-Identifikation
- Optimierte Spaltenreihenfolge
- CSV-Export

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

## 🔧 Installation

### **Virtuelle Umgebung einrichten**
```bash
# 1. Virtuelle Umgebung erstellen
python -m venv venv

# 2. Aktivieren
.\venv\Scripts\Activate.ps1

# 3. Abhängigkeiten installieren
pip install -r requirements.txt
pip install -r requirements_dashboard.txt
```

### **Schnellinstallation (Windows)**
```bash
# Batch-Skript ausführen
.\install_venv.bat

# Oder PowerShell
.\install_venv.ps1
```

## 📁 Projektstruktur

```
Trade_Analysis/
├── src/
│   ├── data_loader.py          # SQLite-Datenlader
│   ├── analysis.py             # Datenanalyse
│   ├── visualization.py        # Visualisierungen
│   └── utils.py                # Hilfsfunktionen
├── config/
│   └── config.ini              # Konfiguration
├── tradelog_dashboard.py       # Hauptdashboard
├── requirements.txt             # Core-Abhängigkeiten
├── requirements_dashboard.txt   # Dashboard-Abhängigkeiten
└── README.md                   # Diese Datei
```

## 🚨 Fehlerbehebung

Bei Problemen siehe: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### **Häufige Probleme:**
- **ModuleNotFoundError**: Virtuelle Umgebung aktivieren
- **SQL Syntax Error**: Wurde behoben - alle Tabellennamen werden korrekt behandelt
- **Datei-Upload-Probleme**: Automatische Bereinigung temporärer Dateien

## 🎯 Nächste Schritte

1. **Dashboard starten** und Ihre `.db3` Datei laden
2. **Trade-Tabelle-Tab** öffnen für vollständige Übersicht
3. **Filter und Sortierung** nach Ihren Bedürfnissen anpassen
4. **Daten exportieren** in gewünschte Formate
5. **Weitere Analysen** in den anderen Tabs durchführen

## 📞 Support

- **Fehlerbehebung**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Installation**: [INSTALLATION.md](INSTALLATION.md)
- **Beispiele**: [example_usage.py](example_usage.py)

---

**Viel Erfolg bei der Trade-Analyse! 🎯📊**
