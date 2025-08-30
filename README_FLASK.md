# 🚀 TAT Analyse Tool - Flask Fork

Ein moderner Flask-basierter Fork des TAT Analyse Tools für die Analyse und Migration von SQLite-Tradelogdateien.

## ✨ Neue Features im Flask-Fork

### 🔄 **Framework-Wechsel**
- **Von Streamlit zu Flask**: Bessere Performance und Skalierbarkeit
- **Moderne Web-Architektur**: RESTful API-Endpunkte
- **Bessere Wartbarkeit**: Klare Trennung von Backend und Frontend

### 🎨 **Verbesserte Benutzeroberfläche**
- **Bootstrap 5**: Modernes, responsives Design
- **Font Awesome Icons**: Professionelle Symbolik
- **Interaktive Charts**: Plotly.js Integration
- **Drag & Drop Upload**: Intuitive Dateiverarbeitung

### 🚀 **Performance-Verbesserungen**
- **Client-seitige Verarbeitung**: Schnellere Filter und Sortierung
- **Paginierung**: Effiziente Handhabung großer Datensätze
- **Caching**: Intelligente Datenverwaltung
- **API-Endpunkte**: Separate Datenzugriffe

## 🛠️ Installation

### **1. Virtuelle Umgebung einrichten**
```bash
# Virtuelle Umgebung erstellen
python -m venv venv_flask

# Aktivieren (Windows)
.\venv_flask\Scripts\Activate.ps1

# Aktivieren (Linux/Mac)
source venv_flask/bin/activate
```

### **2. Abhängigkeiten installieren**
```bash
# Flask-spezifische Requirements installieren
pip install -r requirements_flask.txt
```

### **3. Anwendung starten**
```bash
# Flask-App starten
python app_flask.py
```

Die Anwendung ist dann unter `http://localhost:5000` verfügbar.

## 📁 Projektstruktur

```
TAT_Analyse/
├── app_flask.py                 # Hauptanwendung (Flask)
├── requirements_flask.txt        # Flask-spezifische Abhängigkeiten
├── templates/                   # HTML-Templates
│   ├── base.html               # Basis-Template
│   ├── index.html              # Startseite
│   ├── upload.html             # Upload-Seite
│   ├── dashboard.html          # Dashboard
│   ├── trade_table.html        # Trade-Tabelle
│   ├── 404.html                # 404-Fehlerseite
│   └── 500.html                # 500-Fehlerseite
├── temp_uploads/                # Temporäre Upload-Dateien
├── cache/                       # Cache-Verzeichnis
└── config/                      # Konfigurationsdateien
```

## 🌟 Hauptfunktionen

### **📊 Dashboard**
- **Statistik-Karten**: Übersicht über Datenmenge und Qualität
- **Datenbankübersicht**: Tabelleninformationen und Primärschlüssel
- **Datenqualitätsmetriken**: Fehlende Werte, Duplikate, Datentypen
- **Interaktive Charts**: Histogramme, Korrelationsmatrix, Zeitreihen, Boxplots

### **📈 Trade-Tabelle**
- **Vollständige Datenansicht**: Alle Trade-Daten in übersichtlicher Tabelle
- **Intelligente Filter**: Suche in allen oder spezifischen Spalten
- **Sortierung**: Nach beliebigen Spalten (aufsteigend/absteigend)
- **Paginierung**: Konfigurierbare Zeilenanzahl pro Seite
- **Export-Funktionen**: CSV, Excel, JSON

### **📤 Upload-System**
- **Drag & Drop**: Intuitive Dateiverarbeitung
- **Dateivalidierung**: Automatische Überprüfung von Format und Größe
- **Unterstützte Formate**: .db, .db3, .sqlite, .sqlite3
- **Maximale Größe**: 100 MB

## 🔧 API-Endpunkte

### **Datenzugriff**
- `GET /api/data` - Paginierte Daten mit Filter
- `GET /api/charts/<type>` - Verschiedene Chart-Typen
- `GET /api/export/<format>` - Datenexport in verschiedenen Formaten

### **Parameter**
- `page`: Seitennummer (Standard: 1)
- `per_page`: Zeilen pro Seite (Standard: 50)
- `search`: Suchbegriff
- `column`: Spezifische Spalte für Suche
- `sort`: Sortierspalte
- `order`: Sortierreihenfolge (asc/desc)

## 🎯 Verwendung

### **1. Anwendung starten**
```bash
python app_flask.py
```

### **2. Browser öffnen**
Navigieren Sie zu `http://localhost:5000`

### **3. Datei hochladen**
- Ziehen Sie eine SQLite-Datei in den Upload-Bereich
- Oder klicken Sie auf "Datei auswählen"
- Das Tool lädt automatisch die Trade-Daten

### **4. Daten analysieren**
- **Dashboard**: Übersicht und Statistiken
- **Trade-Tabelle**: Vollständige Datenansicht mit Filter
- **Charts**: Interaktive Visualisierungen

### **5. Daten exportieren**
- Wählen Sie das gewünschte Format (CSV, Excel, JSON)
- Exportieren Sie gefilterte oder alle Daten

## 🔒 Sicherheit

- **Dateivalidierung**: Nur SQLite-Dateien werden akzeptiert
- **Größenbeschränkung**: Maximale Dateigröße von 100 MB
- **Temporäre Speicherung**: Uploads werden sicher verarbeitet
- **CSRF-Schutz**: Flask-WTF Integration

## 🚨 Fehlerbehebung

### **Häufige Probleme**

#### **ModuleNotFoundError**
```bash
# Virtuelle Umgebung aktivieren
.\venv_flask\Scripts\Activate.ps1

# Abhängigkeiten neu installieren
pip install -r requirements_flask.txt
```

#### **Port bereits belegt**
```bash
# Anderen Port verwenden
python app_flask.py --port 5001
```

#### **Datei-Upload-Fehler**
- Überprüfen Sie die Dateigröße (max. 100 MB)
- Stellen Sie sicher, dass es sich um eine SQLite-Datei handelt
- Überprüfen Sie die Dateiintegrität

### **Logs überprüfen**
```bash
# Flask-Logs anzeigen
python app_flask.py --debug
```

## 🔄 Migration von Streamlit

### **Vorteile des Flask-Forks**
1. **Bessere Performance**: Client-seitige Verarbeitung
2. **Skalierbarkeit**: RESTful API-Architektur
3. **Wartbarkeit**: Klare Trennung von Frontend und Backend
4. **Flexibilität**: Einfache Erweiterung um neue Features

### **Gemeinsamkeiten**
- Gleiche Datenanalyse-Funktionalität
- Identische Chart-Typen
- Gleiche Export-Formate
- Kompatible Datenbankformate

## 🚀 Nächste Schritte

### **Geplante Features**
- [ ] Benutzerauthentifizierung
- [ ] Datenbankverbindungen (MySQL, PostgreSQL)
- [ ] Erweiterte Chart-Typen
- [ ] Batch-Verarbeitung
- [ ] API-Dokumentation (Swagger)

### **Beitragen**
1. Fork des Repositories
2. Feature-Branch erstellen
3. Änderungen committen
4. Pull Request einreichen

## 📞 Support

- **Issues**: GitHub Issues verwenden
- **Dokumentation**: Diese README und Code-Kommentare
- **Community**: Diskussionen im Repository

## 📄 Lizenz

Dieser Fork basiert auf dem ursprünglichen TAT Analyse Tool und behält die gleiche Lizenz.

---

**Viel Erfolg mit dem Flask-Fork des TAT Analyse Tools! 🎯📊**
