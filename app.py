import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from io import BytesIO
from db_manager import (
    init_db, cargar_horas, guardar_horas, guardar_asignaciones,
    cargar_asignaciones, descargar_bd_desde_drive, subir_bd_a_drive
)

st.set_page_config(page_title="Inicio", page_icon="🏥", layout="wide", initial_sidebar_state="expanded",
                   menu_items={'Get Help': 'https://www.extremelycoolapp.com/help', 'Report a bug': "https://www.extremelycoolapp.com/bug", 'About': "# Esta es una aplicación para el TFM de Laura P"})

# === CONFIGURA TU FILE_ID DE GOOGLE DRIVE AQUÍ ===
FILE_ID = "1zqAyIB1BLfCc2uH1v29r-clARHoh2o_s"

st.markdown("""
<style>
[data-testid="stSidebarNavItems"] {
    gap: 0.5rem;
    padding: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# Sincronizar base de datos
descargar_bd_desde_drive(FILE_ID)
init_db()

st.title("🩺 Planificador de Turnos de Enfermería")

st.markdown("""
¡Bienvend@!
Esta herramienta permite planificar automáticamente los turnos de enfermería para un rango de fechas personalizado. Navega por cada una de las pestañas para aprender más sobre ellas.
1. Pestaña Asignador
2. Pestaña Generador de demanda
3. Pestaña Visualización turnos
""")
