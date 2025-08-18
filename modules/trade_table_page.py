"""
Trade Table Page Module für Tradelog Dashboard
Zeigt die Trade-Tabelle auf einer separaten Seite an
"""

import streamlit as st
import pandas as pd
from pathlib import Path

def show_trade_table_page(data_loader, db_path):
    """Zeigt die Trade-Tabelle auf einer separaten Seite an."""
    st.header("📈 Trade-Tabelle")
    
    try:
        # Trade-Tabelle laden
        trade_data = data_loader.load_trade_table(db_path)
        st.success(f"✅ Trade-Tabelle geladen: {len(trade_data)} Zeilen, {len(trade_data.columns)} Spalten")
        
        # Metriken
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Gesamt Trades", len(trade_data))
        with col2:
            st.metric("Spalten", len(trade_data.columns))
        with col3:
            st.metric("Datenbank", Path(db_path).name)
        
        # Komplette Tabelle anzeigen
        st.subheader("📊 Komplette Trade-Tabelle")
        st.dataframe(trade_data, use_container_width=True)
        
        # CSV-Export
        csv = trade_data.to_csv(index=False)
        st.download_button(
            label="📥 CSV herunterladen",
            data=csv,
            file_name="trade_tabelle.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Trade-Tabelle: {e}")
        st.info("💡 Verfügbare Tabellen werden angezeigt...")
        
        # Fallback: Verfügbare Tabellen anzeigen
        try:
            db_info = data_loader.get_sqlite_table_info(db_path)
            st.subheader("📋 Verfügbare Tabellen in der Datenbank")
            
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
                        
        except Exception as e2:
            st.error(f"❌ Fehler beim Laden der Tabelleninformationen: {e2}")
