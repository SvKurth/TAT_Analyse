# 🔧 Troubleshooting - Häufige Probleme und Lösungen

## 🚨 **ModuleNotFoundError: No module named 'ta'**

### **Problem:**
Das Dashboard kann nicht gestartet werden, weil das `ta` Modul (Technical Analysis) fehlt.

### **Lösung 1: Fehlende Abhängigkeiten installieren (Empfohlen)**

```bash
# 1. Virtuelle Umgebung aktivieren
.\venv\Scripts\Activate.ps1

# 2. Fehlende Pakete installieren
pip install ta>=0.10.0
pip install yfinance>=0.2.0

# 3. Alle Requirements neu installieren
pip install -r requirements.txt
pip install -r requirements_dashboard.txt
```

### **Lösung 2: Automatisches Installationsskript verwenden**

```bash
# Batch-Skript (Windows)
.\fix_dependencies.bat

# PowerShell-Skript (Windows)
.\fix_dependencies.ps1
```

### **Lösung 3: Vereinfachten DataLoader verwenden**

Falls das `ta` Modul weiterhin Probleme macht, können Sie den vereinfachten DataLoader verwenden:

```python
# In tradelog_dashboard.py, ändern Sie den Import:
# from src.data_loader import DataLoader
from src.data_loader_simple import SimpleDataLoader as DataLoader
```

## 🚨 **ModuleNotFoundError: No module named 'yfinance'**

### **Problem:**
Das Dashboard kann nicht gestartet werden, weil das `yfinance` Modul (Yahoo Finance) fehlt.

### **Lösung:**

```bash
# 1. Virtuelle Umgebung aktivieren
.\venv\Scripts\Activate.ps1

# 2. yfinance installieren
pip install yfinance>=0.2.0

# 3. Alle Requirements neu installieren
pip install -r requirements.txt
pip install -r requirements_dashboard.txt
```

## 🚨 **PermissionError: [WinError 32] Der Prozess kann nicht auf die Datei zugreifen**

### **Problem:**
Beim Hochladen von Dateien tritt ein Fehler auf: "Der Prozess kann nicht auf die Datei zugreifen, da sie von einem anderen Prozess verwendet wird: 'temp_upload.db'"

### **Ursache:**
Windows kann temporäre Dateien nicht löschen, weil sie noch von einem anderen Prozess verwendet werden.

### **Lösung:**

**Das Problem wurde bereits behoben!** Das Dashboard verwendet jetzt:
- ✅ Eindeutige temporäre Dateinamen
- ✅ Sichere Dateiverwaltung
- ✅ Automatische Bereinigung alter Dateien
- ✅ Mehrere Löschversuche mit Wartezeiten

**Falls das Problem weiterhin auftritt:**

```bash
# 1. Dashboard neu starten
# Das Dashboard bereinigt automatisch alte temporäre Dateien

# 2. Manuell bereinigen (falls nötig)
# Suchen Sie nach Dateien wie "temp_upload.db" oder "tradelog_*.db"
# und löschen Sie diese manuell
```

## 🚨 **Fehler beim Laden der Daten: [Errno 9] Bad file descriptor**

### **Problem:**
Beim Hochladen von Dateien tritt ein Fehler auf: "Fehler beim Laden der Daten: [Errno 9] Bad file descriptor"

### **Ursache:**
Fehlerhafte Verwendung von Datei-Deskriptoren bei der temporären Dateiverwaltung.

### **Lösung:**

**Das Problem wurde bereits behoben!** Das Dashboard verwendet jetzt:
- ✅ Einfache und robuste Dateiverwaltung
- ✅ Eindeutige UUID-basierte Dateinamen
- ✅ Keine komplexen Datei-Deskriptoren
- ✅ Sichere Dateioperationen

**Falls das Problem weiterhin auftritt:**

```bash
# 1. Dashboard neu starten
# Das Dashboard bereinigt automatisch alle temporären Dateien

# 2. Manuell bereinigen
# Löschen Sie alle Dateien, die mit "temp_upload_" beginnen
```

## 🚨 **Fehler beim Laden der Daten: near "Order": syntax error**

### **Problem:**
Beim Laden der Daten tritt ein SQL-Syntax-Fehler auf: "near 'Order': syntax error"

### **Ursache:**
"Order" ist ein reserviertes SQL-Schlüsselwort und kann nicht direkt in SQL-Abfragen verwendet werden.

### **Lösung:**

**Das Problem wurde bereits behoben!** Der DataLoader behandelt jetzt:
- ✅ Alle Tabellennamen in Anführungszeichen
- ✅ Reservierte SQL-Schlüsselwörter korrekt
- ✅ Sichere SQL-Abfragen mit `'Tabellenname'`
- ✅ Robuste Datenbankabfragen

**Falls das Problem weiterhin auftritt:**

```bash
# 1. Dashboard neu starten
# Der DataLoader verwendet jetzt sichere SQL-Abfragen

# 2. Überprüfen Sie die Tabellennamen
# Falls Sie eigene SQL-Abfragen schreiben, setzen Sie Tabellennamen in Anführungszeichen
```

## 🚨 **Datumsspalten werden nicht korrekt angezeigt (.NET-Timestamps)**

### **Problem:**
Spalten wie `DateOpened` und `DateClosed` zeigen seltsame Zahlen statt lesbare Daten an.

### **Ursache:**
Diese Spalten enthalten .NET-Timestamps (Ticks seit dem 1. Januar 0001), die in normale Datumsformate konvertiert werden müssen.

### **Lösung:**

**Das Problem wurde bereits behoben!** Der DataLoader konvertiert jetzt automatisch:
- ✅ **DateOpened** und **DateClosed** Spalten
- ✅ Alle Spalten mit "opened" oder "closed" im Namen
- ✅ .NET-Timestamps zu lesbaren Datumsformaten
- ✅ Fallback-Datumskonvertierung bei Problemen

**Wie funktioniert die Konvertierung:**
```python
# .NET-Timestamp zu Datetime
# Formel: (timestamp - 621355968000000000) / 10000000
# 1 Tick = 100 Nanosekunden
```

**Falls das Problem weiterhin auftritt:**

```bash
# 1. Dashboard neu starten
# Der DataLoader konvertiert automatisch alle .NET-Timestamps

# 2. Überprüfen Sie die Spaltennamen
# Stellen Sie sicher, dass die Spalten "DateOpened" oder "DateClosed" heißen
```

## 🔍 **Weitere häufige Probleme**

### **1. Virtuelle Umgebung ist nicht aktiviert**

**Symptom:** Fehlermeldungen über fehlende Module
**Lösung:**
```bash
# Im Projektverzeichnis
.\venv\Scripts\Activate.ps1

# Überprüfen Sie, ob (venv) am Anfang der Zeile steht
(venv) C:\Users\svenk\...\Trade_Analysis>
```

### **2. Pakete können nicht installiert werden**

**Symptom:** pip install schlägt fehl
**Lösung:**
```bash
# pip aktualisieren
python -m pip install --upgrade pip

# Cache leeren
pip cache purge

# Mit --force-reinstall versuchen
pip install --force-reinstall -r requirements.txt
```

### **3. Streamlit startet nicht**

**Symptom:** `streamlit` Befehl wird nicht erkannt
**Lösung:**
```bash
# Streamlit neu installieren
pip uninstall streamlit
pip install streamlit

# Version prüfen
streamlit --version
```

### **4. Plotly-Charts werden nicht angezeigt**

**Symptom:** Leere Bereiche statt Charts
**Lösung:**
```bash
# Plotly neu installieren
pip uninstall plotly
pip install plotly

# Browser-Cache leeren
# Neustart des Dashboards
```

### **5. PowerShell Execution Policy**

**Symptom:** Skripte können nicht ausgeführt werden
**Lösung:**
```powershell
# Execution Policy prüfen
Get-ExecutionPolicy

# Temporär ändern (nur für aktuelle Session)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Oder für aktuellen Prozess
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

## 🛠️ **Schnelle Reparatur**

### **Alle Probleme auf einmal lösen:**

```bash
# 1. Virtuelle Umgebung aktivieren
.\venv\Scripts\Activate.ps1

# 2. Alle Pakete neu installieren
pip install --upgrade --force-reinstall -r requirements.txt
pip install --upgrade --force-reinstall -r requirements_dashboard.txt

# 3. Installation testen
python -c "import yfinance, ta, streamlit, pandas, plotly; print('Alle Pakete OK!')"

# 4. Dashboard starten
streamlit run tradelog_dashboard.py
```

### **Falls nichts hilft - Komplett neu aufsetzen:**

```bash
# 1. Virtuelle Umgebung deaktivieren
deactivate

# 2. venv-Verzeichnis löschen
rmdir /s venv  # Windows
# oder
rm -rf venv    # Linux/Mac

# 3. Neu erstellen (siehe Schritt 2-6)
```

## 📋 **Überprüfungsliste**

### **Vor dem Start des Dashboards:**

- [ ] Virtuelle Umgebung ist aktiviert (`(venv)` sichtbar)
- [ ] Alle Pakete sind installiert (`pip list` zeigt alle benötigten Pakete)
- [ ] Python-Version ist 3.8+ (`python --version`)
- [ ] pip ist aktuell (`pip --version`)

### **Nach dem Start des Dashboards:**

- [ ] Dashboard lädt ohne Fehlermeldungen
- [ ] Datei-Upload funktioniert
- [ ] Charts werden angezeigt
- [ ] Export-Funktionen funktionieren

## 📞 **Support**

### **Wenn nichts hilft:**

1. **Logs prüfen:**
   ```bash
   streamlit run tradelog_dashboard.py --logger.level debug
   ```

2. **Python-Umgebung prüfen:**
   ```bash
   python -c "import sys; print(sys.path)"
   ```

3. **Paket-Versionen prüfen:**
   ```bash
   pip freeze
   ```

4. **Neue virtuelle Umgebung erstellen:**
   ```bash
   python -m venv venv_new
   .\venv_new\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install -r requirements_dashboard.txt
   ```

### **Hilfreiche Befehle:**

```bash
# Alle installierten Pakete anzeigen
pip list

# Spezifisches Paket prüfen
pip show ta
pip show yfinance

# Paket neu installieren
pip install --force-reinstall ta
pip install --force-reinstall yfinance

# Abhängigkeiten prüfen
pip check
```

---

**Viel Erfolg bei der Fehlerbehebung! 🎯🔧**
