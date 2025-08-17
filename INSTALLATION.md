# 🚀 Installation in virtueller Umgebung (venv)

## Übersicht

Diese Anleitung zeigt Ihnen, wie Sie das Trade_Analysis Projekt in einer virtuellen Python-Umgebung installieren und einrichten.

## 📋 Voraussetzungen

- Python 3.8 oder höher
- pip (Python Package Installer)
- Git (optional, für Repository-Klon)

## 🛠️ Schritt-für-Schritt Installation

### 1. Projektverzeichnis öffnen

```bash
# Falls Sie das Repository klonen möchten:
git clone <repository-url>
cd Trade_Analysis

# Oder falls Sie bereits im Projektverzeichnis sind:
cd Trade_Analysis
```

### 2. Virtuelle Umgebung erstellen

```bash
# Virtuelle Umgebung erstellen
python -m venv venv
```

**Hinweis:** Der Name "venv" ist eine Konvention, Sie können auch einen anderen Namen wählen.

### 3. Virtuelle Umgebung aktivieren

#### Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt):
```cmd
.\venv\Scripts\activate.bat
```

#### Linux/Mac:
```bash
source venv/bin/activate
```

**Erfolgreiche Aktivierung erkennen Sie am `(venv)` Präfix in der Kommandozeile:**

```bash
(venv) C:\Users\svenk\OneDrive\Dokumente\000_Python_Entwicklung\Trade_Analysis>
```

### 4. pip aktualisieren (empfohlen)

```bash
python -m pip install --upgrade pip
```

### 5. Basis-Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 6. Dashboard-Abhängigkeiten installieren

```bash
pip install -r requirements_dashboard.txt
```

### 7. Installation überprüfen

```bash
# Überprüfen Sie, ob alle Pakete installiert sind
pip list

# Oder spezifische Pakete prüfen
python -c "import streamlit, pandas, plotly; print('Alle Pakete erfolgreich installiert!')"
```

## 🎯 **Verwendung der virtuellen Umgebung**

### **Aktivierung bei jedem neuen Terminal:**

```bash
# Im Projektverzeichnis
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# oder
.\venv\Scripts\activate.bat  # Windows CMD
# oder
source venv/bin/activate     # Linux/Mac
```

### **Deaktivierung:**

```bash
deactivate
```

## 🚀 **Projekt starten**

### **1. DataLoader testen:**

```bash
# Virtuelle Umgebung aktivieren
.\venv\Scripts\Activate.ps1

# Beispielskript ausführen
python example_tradelog_loader.py
```

### **2. Dashboard starten:**

```bash
# Virtuelle Umgebung aktivieren
.\venv\Scripts\Activate.ps1

# Dashboard starten
streamlit run tradelog_dashboard.py
```

Das Dashboard öffnet sich automatisch in Ihrem Browser unter `http://localhost:8501`

## 📁 **Projektstruktur nach Installation**

```
Trade_Analysis/
├── venv/                          # Virtuelle Umgebung
├── src/                           # Quellcode
│   ├── __init__.py
│   ├── data_loader.py            # Erweiterter DataLoader
│   ├── analysis.py
│   ├── utils.py
│   └── visualization.py
├── config/                        # Konfigurationsdateien
│   ├── config.ini
│   └── tradelog_config.ini
├── output/                        # Ausgabeverzeichnis (wird erstellt)
├── logs/                          # Log-Verzeichnis (wird erstellt)
├── requirements.txt               # Basis-Abhängigkeiten
├── requirements_dashboard.txt     # Dashboard-Abhängigkeiten
├── example_tradelog_loader.py    # Beispielskript
├── tradelog_dashboard.py         # Interaktives Dashboard
├── main.py                       # Hauptprogramm
└── README.md
```

## 🔧 **Fehlerbehebung**

### **Häufige Probleme:**

#### 1. **Virtuelle Umgebung kann nicht aktiviert werden**
```bash
# PowerShell Execution Policy prüfen
Get-ExecutionPolicy

# Falls restriktiv, temporär ändern:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. **Pakete können nicht installiert werden**
```bash
# pip aktualisieren
python -m pip install --upgrade pip

# Cache leeren
pip cache purge

# Mit --force-reinstall versuchen
pip install --force-reinstall -r requirements.txt
```

#### 3. **Streamlit startet nicht**
```bash
# Streamlit neu installieren
pip uninstall streamlit
pip install streamlit

# Version prüfen
streamlit --version
```

#### 4. **Plotly-Charts werden nicht angezeigt**
```bash
# Plotly neu installieren
pip uninstall plotly
pip install plotly

# Browser-Cache leeren
```

### **Logs prüfen:**

```bash
# Streamlit-Logs anzeigen
streamlit run tradelog_dashboard.py --logger.level debug
```

## 🧹 **Wartung der virtuellen Umgebung**

### **Pakete aktualisieren:**

```bash
# Alle Pakete auf neueste Version aktualisieren
pip list --outdated
pip install --upgrade <package-name>

# Oder alle Pakete aktualisieren
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements_dashboard.txt
```

### **Virtuelle Umgebung löschen und neu erstellen:**

```bash
# Deaktivieren
deactivate

# Verzeichnis löschen
rmdir /s venv  # Windows
# oder
rm -rf venv    # Linux/Mac

# Neu erstellen (siehe Schritt 2-6)
```

## 📱 **IDE-Integration**

### **VS Code:**
1. `Ctrl+Shift+P` → "Python: Select Interpreter"
2. Wählen Sie den Python-Interpreter aus dem `venv`-Verzeichnis
3. Terminal öffnen → Automatische Aktivierung der venv

### **PyCharm:**
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Pfad zu `venv/Scripts/python.exe` (Windows) oder `venv/bin/python` (Linux/Mac)

## 🔒 **Sicherheit**

- Die virtuelle Umgebung isoliert Projektabhängigkeiten
- Keine Konflikte mit anderen Python-Projekten
- Einfache Reproduzierbarkeit der Entwicklungsumgebung

## 📞 **Support**

Bei Installationsproblemen:

1. **Überprüfen Sie die Python-Version:** `python --version`
2. **Überprüfen Sie pip:** `pip --version`
3. **Überprüfen Sie die venv-Aktivierung:** `(venv)` sollte in der Kommandozeile erscheinen
4. **Überprüfen Sie die installierten Pakete:** `pip list`

---

**Viel Erfolg bei der Installation! 🎯🚀**
