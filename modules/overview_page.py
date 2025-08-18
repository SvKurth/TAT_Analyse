"""
Overview Page Module für Tradelog Dashboard
Zeigt die Übersichtsseite mit Datenbankinformationen
"""

import streamlit as st
import pandas as pd
from pathlib import Path

def show_overview_page(data_loader, db_path):
    """Zeigt die Übersichtsseite an."""
    st.header("📋 Übersicht")
    st.write("Willkommen beim Tradelog Dashboard!")
    
    try:
        # Datenbankinformationen anzeigen
        db_info = data_loader.get_sqlite_table_info(db_path)
        st.subheader("🗄️ Datenbankdetails")
        st.write(f"**Pfad:** {db_path}")
        st.write(f"**Größe:** {Path(db_path).stat().st_size / 1024 / 1024:.2f} MB")
        
        # Verfügbare Tabellen
        st.subheader("📋 Verfügbare Tabellen")
        for table_name, table_info in db_info['tables'].items():
            with st.expander(f"📊 {table_name} ({table_info['row_count']} Zeilen)"):
                st.write(f"**Spalten:** {len(table_info['columns'])}")
                
                # Spaltenliste
                st.write("**Spalten:**")
                for col in table_info['columns']:
                    pk_indicator = " 🔑" if col.get('pk', 0) > 0 else ""
                    st.write(f"- {col['name']} ({col['type']}){pk_indicator}")
                
                # Beispieldaten
                if table_info['sample_data']:
                    st.write("**Beispieldaten:**")
                    sample_df = pd.DataFrame(table_info['sample_data'], columns=table_info['column_names'])
                    st.dataframe(sample_df, use_container_width=True)
                    
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Datenbankinformationen: {e}")
