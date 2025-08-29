# Troubleshooting Guide

## Häufige Fehler und deren Lösungen

### ❌ Fehler: "cannot insert DateOpened, already exists"

**Problem:** Dieser Fehler tritt auf, wenn die Monatskalenderansicht geladen wird und es Probleme mit der DateOpened-Spalte in der Datenbank gibt.

**Ursachen:**
1. Doppelte Spaltennamen in der Datenbank
2. Konflikte bei der Datumskonvertierung
3. Probleme mit der .NET-Timestamp-Konvertierung
4. Datenbankintegritätsprobleme

**Lösungen:**

#### 1. Sofortige Behebung
Der Fehler wurde in der neuesten Version automatisch behoben. Die Anwendung sollte jetzt robuster mit DateOpened-Problemen umgehen.

#### 2. Manuelle Datenbankprüfung
```sql
-- Prüfe auf doppelte Spaltennamen
SELECT name, COUNT(*) as count 
FROM pragma_table_info('Trade') 
GROUP BY name 
HAVING COUNT(*) > 1;

-- Prüfe die Struktur der Trade-Tabelle
PRAGMA table_info(Trade);
```

#### 3. Datenbank neu erstellen (falls nötig)
```bash
# Sichere die ursprüngliche Datenbank
cp trades.db trades_backup.db

# Lösche die problematische Datenbank
rm trades.db

# Starte die Anwendung neu - sie wird eine neue Datenbank erstellen
```

#### 4. Debug-Informationen aktivieren
Die Anwendung zeigt jetzt automatisch Debug-Informationen an, wenn der Fehler auftritt. Diese helfen bei der Identifikation des Problems.

### 🔧 Weitere Verbesserungen

#### Verbesserte Fehlerbehandlung
- Automatische Erkennung von DateOpened-Problemen
- Fallback-Mechanismen für fehlgeschlagene Datumskonvertierungen
- Bessere Logging-Informationen

#### Robuste Datenverarbeitung
- Prüfung auf bereits konvertierte Spalten
- Automatische Bereinigung von doppelten Spaltennamen
- Graceful Degradation bei Fehlern

### 📋 Vorbeugende Maßnahmen

1. **Regelmäßige Backups:** Sichere deine Datenbank regelmäßig
2. **Datenvalidierung:** Prüfe neue Daten vor dem Import
3. **Versionierung:** Verwende immer die neueste Version der Anwendung

### 🆘 Bei anhaltenden Problemen

1. **Logs prüfen:** Schaue in die `logs/app.log` Datei
2. **Debug-Modus:** Die Anwendung zeigt jetzt automatisch Debug-Informationen
3. **Datenbank-Reset:** Als letzter Ausweg - lösche die Datenbank und starte neu

### 📞 Support

Falls der Fehler weiterhin auftritt:
1. Sammle alle Debug-Informationen
2. Prüfe die Log-Dateien
3. Erstelle ein Issue mit detaillierten Informationen

---

**Hinweis:** Die neueste Version der Anwendung sollte den "DateOpened already exists" Fehler automatisch beheben. Falls der Fehler weiterhin auftritt, liegt möglicherweise ein tieferliegendes Problem mit der Datenbankstruktur vor.
