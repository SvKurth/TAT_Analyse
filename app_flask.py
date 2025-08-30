#!/usr/bin/env python3
"""
TAT Analyse Tool - Flask Fork
Hauptanwendung mit Flask Web-Framework
"""

import os
import sys
from pathlib import Path
import tempfile
import uuid
import time
import json
from datetime import datetime
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.utils

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import io

# Projektverzeichnisse zum Python-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Bestehende Services importieren (optional)
try:
    from app.services.trade_data_service import TradeDataService
except ImportError:
    TradeDataService = None
    print("⚠️ TradeDataService nicht verfügbar")

try:
    from src.utils import load_config
except ImportError:
    load_config = None
    print("⚠️ load_config nicht verfügbar")

# Flask-App initialisieren
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Für Produktion ändern!
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['CACHE_FOLDER'] = 'cache'

# Upload-Ordner erstellen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CACHE_FOLDER'], exist_ok=True)

# Globale Variablen
current_db_path = None
current_data = None
current_tables = None

# Einfacher Konfigurationsmanager für die Dateiauswahl
class SimpleConfigManager:
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.last_file_config = self.config_dir / "last_file.txt"
        self.auto_load_config = self.config_dir / "auto_load.txt"
        
        # Stelle sicher, dass beide Konfigurationsdateien existieren
        self._ensure_config_files_exist()
    
    def _ensure_config_files_exist(self):
        """Stellt sicher, dass alle Konfigurationsdateien existieren"""
        try:
            # Auto-Load-Datei erstellen falls nicht vorhanden
            if not self.auto_load_config.exists():
                self.save_auto_load_setting(True)
                print("✅ Auto-Load-Datei erstellt")
            
            # Last-File-Datei erstellen falls nicht vorhanden (mit leerem Inhalt)
            if not self.last_file_config.exists():
                with open(self.last_file_config, 'w', encoding='utf-8') as f:
                    f.write("")
                print("✅ Last-File-Datei erstellt (leer)")
                
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Konfigurationsdateien: {e}")
    
    def save_last_file_path(self, file_path):
        """Speichert den zuletzt verwendeten Dateipfad"""
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            self.config_dir.mkdir(exist_ok=True)
            
            # Datei schreiben
            with open(self.last_file_config, 'w', encoding='utf-8') as f:
                f.write(str(file_path))
            
            print(f"✅ Dateipfad gespeichert: {file_path}")
            print(f"📁 Datei gespeichert in: {self.last_file_config}")
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern des Dateipfads: {e}")
            print(f"📁 Verzeichnis: {self.config_dir}")
            print(f"📁 Datei: {self.last_file_config}")
            return False
    
    def get_last_file_path(self):
        """Holt den zuletzt verwendeten Dateipfad"""
        try:
            if self.last_file_config.exists():
                with open(self.last_file_config, 'r', encoding='utf-8') as f:
                    path = f.read().strip()
                    if path and os.path.exists(path):
                        print(f"✅ Gespeicherten Pfad gefunden: {path}")
                        return path
                    elif path:
                        print(f"⚠️ Gespeicherter Pfad existiert nicht mehr: {path}")
                    else:
                        print("ℹ️ Last-File-Datei ist leer")
            else:
                print("⚠️ Last-File-Datei existiert nicht")
            return None
            
        except Exception as e:
            print(f"❌ Fehler beim Lesen des Dateipfads: {e}")
            return None
    
    def save_auto_load_setting(self, enabled):
        """Speichert die Auto-Load-Einstellung"""
        try:
            with open(self.auto_load_config, 'w', encoding='utf-8') as f:
                f.write(str(enabled))
            print(f"✅ Auto-Load-Einstellung gespeichert: {enabled}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Speichern der Auto-Load-Einstellung: {e}")
            return False
    
    def get_auto_load_setting(self):
        """Holt die Auto-Load-Einstellung"""
        try:
            if self.auto_load_config.exists():
                with open(self.auto_load_config, 'r', encoding='utf-8') as f:
                    setting = f.read().strip().lower()
                    return setting in ['true', '1', 'yes', 'on']
            return False
        except Exception as e:
            print(f"❌ Fehler beim Lesen der Auto-Load-Einstellung: {e}")
            return False

# Konfigurationsmanager initialisieren
config_manager = SimpleConfigManager()

# Context Processor für globale Template-Variablen
@app.context_processor
def inject_global_vars():
    """Injiziert globale Variablen in alle Templates"""
    return {
        'current_data': current_data,
        'current_tables': current_tables,
        'current_db_path': current_db_path
    }

# Jinja2-Globals für Template-Funktionen
@app.template_global()
def min_value(a, b):
    """Min-Funktion für Templates"""
    return min(a, b)

@app.template_global()
def max_value(a, b):
    """Max-Funktion für Templates"""
    return max(a, b)

@app.template_global()
def abs_value(value):
    """Template global für abs() Funktion"""
    if value is None:
        return 0
    return abs(value)

# Test-Route für Debugging
@app.route('/test')
def test():
    """Test-Route für Debugging"""
    return jsonify({
        'status': 'ok',
        'message': 'Flask-App läuft korrekt',
        'current_data': current_data is not None,
        'current_tables': current_tables is not None,
        'current_db_path': current_db_path,
        'data_shape': current_data.shape if current_data is not None else None,
        'tables_count': len(current_tables) if current_tables else 0
    })

# Debug-Route für Upload-Status
@app.route('/debug/upload')
def debug_upload():
    """Debug-Route für Upload-Status"""
    upload_files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file)
            if os.path.isfile(filepath):
                upload_files.append({
                    'name': file,
                    'size': os.path.getsize(filepath),
                    'path': filepath,
                    'is_sqlite': is_valid_sqlite_file(filepath) if file.endswith(('.db', '.db3', '.sqlite', '.sqlite3')) else False
                })
    
    return jsonify({
        'upload_folder': app.config['UPLOAD_FOLDER'],
        'upload_files': upload_files,
        'current_data': current_data is not None,
        'current_tables': current_tables is not None,
        'current_db_path': current_db_path
    })

# Hilfsfunktionen
def is_valid_sqlite_file(filepath):
    """Überprüft ob eine Datei eine gültige SQLite-Datenbank ist - robuster wie in Streamlit"""
    try:
        # Überprüfe Dateigröße (SQLite-Dateien sind mindestens 512 Bytes)
        if os.path.getsize(filepath) < 512:
            print(f"❌ Datei zu klein für SQLite: {os.path.getsize(filepath)} Bytes")
            return False
        
        # Versuche SQLite-Verbindung zu öffnen
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        # Überprüfe ob es sich um eine SQLite-Datenbank handelt
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()
        print(f"✅ SQLite-Version: {version[0] if version else 'Unbekannt'}")
        
        # Überprüfe ob Tabellen vorhanden sind
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Anzahl Tabellen: {len(tables)}")
        
        conn.close()
        
        if len(tables) == 0:
            print("❌ Keine Tabellen in der Datenbank gefunden")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei SQLite-Validierung: {e}")
        return False

def find_trade_table(db_path):
    """Findet die Trade-Tabelle - robuster wie in Streamlit"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Alle Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"🔍 Verfügbare Tabellen: {tables}")
        
        # Priorität: "Trade" oder "trade"
        target_table = None
        for table in tables:
            if table.lower() == "trade":
                target_table = table
                print(f"🎯 Trade-Tabelle gefunden: {table}")
                break
        
        if not target_table:
            # Fallback: erste verfügbare Tabelle
            target_table = tables[0] if tables else None
            print(f"⚠️ Verwende Fallback-Tabelle: {target_table}")
        
        conn.close()
        return target_table
        
    except Exception as e:
        print(f"❌ Fehler beim Finden der Trade-Tabelle: {e}")
        return None

def get_db_info(db_path):
    """Holt Informationen über die Datenbank"""
    try:
        print(f"🔍 Hole Datenbankinformationen für: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Gefundene Tabellen: {tables}")
        
        # Informationen über jede Tabelle sammeln
        table_info = {}
        for table in tables:
            print(f"📊 Analysiere Tabelle: {table}")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            table_info[table] = {
                'columns': [col[1] for col in columns],
                'types': [col[2] for col in columns],
                'primary_keys': [col[1] for col in columns if col[5] == 1]
            }
            
            # Anzahl der Zeilen
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            table_info[table]['row_count'] = row_count
            
            print(f"   📋 Spalten: {len(table_info[table]['columns'])}")
            print(f"   📊 Zeilen: {table_info[table]['row_count']}")
            print(f"   🔑 Primärschlüssel: {table_info[table]['primary_keys']}")
        
        conn.close()
        print(f"✅ Datenbankinformationen erfolgreich geladen")
        return table_info
        
    except Exception as e:
        print(f"❌ Fehler beim Abrufen der Datenbankinformationen: {e}")
        return {}

def load_trade_data(db_path, table_name="Trade"):
    """Lädt Trade-Daten aus der Datenbank - robuster wie in Streamlit"""
    try:
        print(f"🔍 Verbinde mit Datenbank: {db_path}")
        
        # Trade-Tabelle finden
        target_table = find_trade_table(db_path)
        if not target_table:
            print("❌ Keine Trade-Tabelle in der Datenbank gefunden")
            return None, "Keine Trade-Tabelle in der Datenbank gefunden"
        
        # Daten laden
        print(f"📊 Lade Daten aus Tabelle: {target_table}")
        conn = sqlite3.connect(db_path)
        
        # Prüfe ob Tabelle existiert und Daten hat
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
        row_count = cursor.fetchone()[0]
        print(f"📊 Zeilen in Tabelle: {row_count}")
        
        if row_count == 0:
            print("⚠️ Tabelle ist leer")
            conn.close()
            return pd.DataFrame(), target_table  # Leerer DataFrame zurückgeben
        
        # Spalteninformationen holen
        cursor.execute(f"PRAGMA table_info({target_table})")
        columns_info = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        print(f"📋 Spalten: {columns}")
        
        # Daten laden
        query = f"SELECT * FROM {target_table}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Prüfe ob DataFrame leer ist
        if df is None or df.empty:
            print("⚠️ DataFrame ist leer")
            return pd.DataFrame(), target_table
        
        # Prüfe ob DataFrame Spalten hat
        if len(df.columns) == 0:
            print("⚠️ DataFrame hat keine Spalten")
            return pd.DataFrame(), target_table
        
        print(f"✅ Daten erfolgreich geladen: {len(df)} Zeilen, {len(df.columns)} Spalten")
        print(f"📋 Spalten: {list(df.columns)}")
        
        return df, target_table
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Trade-Daten: {e}")
        return None, str(e)

def create_charts(df, table_name):
    """Erstellt verschiedene Charts für die Daten - robuster wie in Streamlit"""
    charts = {}
    
    try:
        # Prüfe ob DataFrame gültig ist
        if df is None or df.empty:
            print("⚠️ Keine Daten für Charts verfügbar")
            return charts
        
        # Numerische Spalten identifizieren
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        date_columns = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        print(f"📊 Erstelle Charts für {len(numeric_columns)} numerische und {len(date_columns)} Datumsspalten")
        
        # 1. Histogramm für numerische Spalten
        if numeric_columns:
            try:
                fig_hist = make_subplots(
                    rows=len(numeric_columns), cols=1,
                    subplot_titles=numeric_columns,
                    vertical_spacing=0.1
                )
                
                for i, col in enumerate(numeric_columns, 1):
                    # Prüfe ob Spalte Daten hat
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        fig_hist.add_trace(
                            go.Histogram(x=col_data, name=col),
                            row=i, col=1
                        )
                
                fig_hist.update_layout(height=200 * len(numeric_columns), title_text="Verteilungen")
                charts['histogram'] = json.dumps(fig_hist, cls=plotly.utils.PlotlyJSONEncoder)
                print(f"✅ Histogramm erstellt")
            except Exception as e:
                print(f"❌ Fehler beim Erstellen des Histogramms: {e}")
        
        # 2. Korrelationsmatrix
        if len(numeric_columns) > 1:
            try:
                corr_matrix = df[numeric_columns].corr()
                fig_corr = px.imshow(
                    corr_matrix,
                    title="Korrelationsmatrix",
                    color_continuous_scale='RdBu'
                )
                charts['correlation'] = json.dumps(fig_corr, cls=plotly.utils.PlotlyJSONEncoder)
                print(f"✅ Korrelationsmatrix erstellt")
            except Exception as e:
                print(f"❌ Fehler beim Erstellen der Korrelationsmatrix: {e}")
        
        # 3. Zeitreihe (falls Datumsspalte vorhanden)
        if date_columns and numeric_columns:
            try:
                date_col = date_columns[0]
                numeric_col = numeric_columns[0]
                
                # Prüfe ob Datumsspalte gültige Daten hat
                valid_data = df.dropna(subset=[date_col, numeric_col])
                if len(valid_data) > 0:
                    fig_time = px.line(
                        valid_data.sort_values(date_col),
                        x=date_col,
                        y=numeric_col,
                        title=f"Zeitreihe: {numeric_col} über {date_col}"
                    )
                    charts['timeseries'] = json.dumps(fig_time, cls=plotly.utils.PlotlyJSONEncoder)
                    print(f"✅ Zeitreihe erstellt")
                else:
                    print(f"⚠️ Keine gültigen Daten für Zeitreihe")
            except Exception as e:
                print(f"❌ Fehler beim Erstellen der Zeitreihe: {e}")
        
        # 4. Boxplot für numerische Spalten
        if numeric_columns:
            try:
                fig_box = px.box(
                    df[numeric_columns],
                    title="Boxplots der numerischen Spalten"
                )
                charts['boxplot'] = json.dumps(fig_box, cls=plotly.utils.PlotlyJSONEncoder)
                print(f"✅ Boxplot erstellt")
            except Exception as e:
                print(f"❌ Fehler beim Erstellen des Boxplots: {e}")
        
        print(f"✅ {len(charts)} Charts erfolgreich erstellt")
        
    except Exception as e:
        print(f"❌ Allgemeiner Fehler beim Erstellen der Charts: {e}")
    
    return charts

# Flask-Routen
@app.route('/')
def index():
    """Hauptseite"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Datei-Upload-Handler"""
    global current_db_path, current_data, current_tables
    
    print(f"=== UPLOAD ROUTE AUFGERUFEN ===")
    print(f"Request-Methode: {request.method}")
    print(f"Request-URL: {request.url}")
    print(f"Request-Files: {list(request.files.keys()) if request.files else 'Keine'}")
    
    if request.method == 'POST':
        print(f"POST-Request empfangen")
        print(f"Files im Request: {request.files}")
        print(f"Form-Daten: {request.form}")
        
        if 'file' not in request.files:
            print(f"❌ Keine Datei im Request gefunden")
            flash('Keine Datei ausgewählt')
            return redirect(request.url)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Keine Datei ausgewählt')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Keine Datei ausgewählt')
            return redirect(request.url)
        
        if file:
            try:
                # Datei speichern
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                print(f"📁 Datei gespeichert: {filepath}")
                print(f"📊 Dateigröße: {os.path.getsize(filepath)} Bytes")
                
                # Überprüfen ob es eine gültige SQLite-Datei ist
                print(f"🔍 Validiere SQLite-Datei: {filename}")
                if not is_valid_sqlite_file(filepath):
                    print(f"❌ Datei {filename} ist keine gültige SQLite-Datenbank")
                    flash(f'Die Datei {filename} ist keine gültige SQLite-Datenbank. Bitte wählen Sie eine .db, .db3, .sqlite oder .sqlite3 Datei aus.')
                    # Datei löschen
                    os.remove(filepath)
                    return redirect(request.url)
                
                print(f"✅ SQLite-Validierung erfolgreich")
                
                # Datenbank laden
                current_db_path = filepath
                print(f"🔍 Lade Datenbankinformationen...")
                current_tables = get_db_info(filepath)
                print(f"📋 Gefundene Tabellen: {list(current_tables.keys()) if current_tables else 'Keine'}")
                
                # Trade-Daten laden
                print(f"📊 Lade Trade-Daten...")
                current_data, table_name = load_trade_data(filepath)
                
                if current_data is not None:
                    print(f"✅ Daten erfolgreich geladen: {len(current_data)} Zeilen, {len(current_data.columns)} Spalten")
                    
                    # Prüfe ob DataFrame leer ist
                    if current_data.empty:
                        print("⚠️ DataFrame ist leer - aber das ist OK")
                        flash(f'Datei geladen: {filename} (Tabelle ist leer)')
                    else:
                        flash(f'Datei erfolgreich geladen: {filename} ({len(current_data)} Zeilen)')
                    
                    # Konfiguration speichern
                    config_manager.save_last_file_path(filepath)
                    
                    return redirect(url_for('dashboard'))
                else:
                    print(f"❌ Fehler beim Laden der Daten: {table_name}")
                    flash(f'Fehler beim Laden der Daten: {table_name}')
                    # Datei löschen
                    os.remove(filepath)
                    return redirect(request.url)
                    
            except Exception as e:
                print(f"❌ Fehler beim Verarbeiten der Datei: {str(e)}")
                flash(f'Fehler beim Verarbeiten der Datei: {str(e)}')
                # Datei löschen falls vorhanden
                if 'filepath' in locals() and os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard-Hauptseite"""
    global current_db_path, current_data, current_tables
    
    if current_data is None:
        flash('Bitte laden Sie zuerst eine Datenbankdatei')
        return redirect(url_for('upload_file'))
    
    # Charts erstellen (nur wenn Daten vorhanden)
    charts = {}
    if current_data is not None and not current_data.empty:
        charts = create_charts(current_data, "Trade")
    
    return render_template('dashboard.html', 
                         data=current_data, 
                         tables=current_tables,
                         charts=charts)

@app.route('/trade_table')
def trade_table():
    """Trade-Tabelle-Seite"""
    global current_data, current_tables
    
    if current_data is None:
        flash('Bitte laden Sie zuerst eine Datenbankdatei')
        return redirect(url_for('upload_file'))
    
    return render_template('trade_table.html', 
                         data=current_data, 
                         tables=current_tables)

@app.route('/metrics')
def metrics():
    """Metriken-Seite"""
    global current_data, current_tables
    
    if current_data is None:
        flash('Bitte laden Sie zuerst eine Datenbankdatei')
        return redirect(url_for('upload_file'))
    
    return render_template('metrics.html', 
                         data=current_data, 
                         tables=current_tables)



@app.route('/monthly_calendar')
def monthly_calendar():
    """Monatskalender-Seite"""
    global current_data, current_tables
    
    if current_data is None:
        flash('Bitte laden Sie zuerst eine Datenbankdatei')
        return redirect(url_for('upload_file'))
    
    return render_template('monthly_calendar.html', 
                         data=current_data, 
                         tables=current_tables)

@app.route('/navigator')
def navigator():
    """TAT Tradenavigator-Seite"""
    global current_data, current_tables
    
    if current_data is None:
        flash('Bitte laden Sie zuerst eine Datenbankdatei')
        return redirect(url_for('upload_file'))
    
    return render_template('navigator.html', 
                         data=current_data, 
                         tables=current_tables)

@app.route('/performance')
def performance():
    """Performance Dashboard-Seite"""
    global current_data, current_tables
    
    if current_data is None:
        flash('Bitte laden Sie zuerst eine Datenbankdatei')
        return redirect(url_for('upload_file'))
    
    return render_template('performance.html', 
                         data=current_data, 
                         tables=current_tables)

@app.route('/api/data')
def get_data():
    """API-Endpunkt für Daten"""
    global current_data
    
    if current_data is None:
        return jsonify({'error': 'Keine Daten geladen'}), 400
    
    # Paginierung
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    page_data = current_data.iloc[start_idx:end_idx]
    
    return jsonify({
        'data': page_data.to_dict('records'),
        'total_rows': len(current_data),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(current_data) + per_page - 1) // per_page
    })

@app.route('/api/export/<format>')
def export_data(format):
    """API-Endpunkt für Datenexport"""
    global current_data
    
    if current_data is None:
        return jsonify({'error': 'Keine Daten geladen'}), 400
    
    try:
        if format == 'csv':
            output = io.StringIO()
            current_data.to_csv(output, index=False)
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name='trade_data.csv'
            )
        
        elif format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                current_data.to_excel(writer, index=False, sheet_name='Trade_Data')
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='trade_data.xlsx'
            )
        
        elif format == 'json':
            return jsonify(current_data.to_dict('records'))
        
        else:
            return jsonify({'error': 'Unterstütztes Format nicht gefunden'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/<chart_type>')
def get_chart(chart_type):
    """API-Endpunkt für Charts"""
    global current_data
    
    if current_data is None:
        return jsonify({'error': 'Keine Daten geladen'}), 400
    
    charts = create_charts(current_data, "Trade")
    
    if chart_type in charts:
        return charts[chart_type]
    else:
        return jsonify({'error': 'Chart-Typ nicht gefunden'}), 404

# Fehlerbehandlung
@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Datei zu groß (Maximum: 100MB)'}), 413

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Auto-Load der letzten Datei
    if config_manager.get_auto_load_setting():
        last_file = config_manager.get_last_file_path()
        if last_file and os.path.exists(last_file):
            print(f"🔄 Auto-Load der letzten Datei: {last_file}")
            current_db_path = last_file
            current_tables = get_db_info(last_file)
            current_data, _ = load_trade_data(last_file)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
