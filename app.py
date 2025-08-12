import streamlit as st
from config import setup_page
import pandas as pd
from datetime import datetime, timedelta, date
from io import BytesIO
from db_manager import (
    init_db, cargar_horas, guardar_horas, guardar_asignaciones,
    cargar_asignaciones, descargar_bd_desde_drive, subir_bd_a_drive
)


st.set_page_config(  # ← Esto es imprescindible
    page_title="MUGYPS",  # Título en la pestaña del navegador
    page_icon="🧊",       # Icono
    layout="wide",        # Diseño
    initial_sidebar_state="expanded"  # Sidebar visible
)

# 2. Eliminar el texto "app" del menú automático superior
# 2. Solución definitiva para eliminar "app" (sin reemplazo)
st.markdown("""
<style>
    /* Elimina solo el texto "app" del menú superior */
    [data-testid="stSidebarNav"] + div [data-testid="stVerticalBlock"] > div:first-child {
        height: 0px !important;
        visibility: hidden !important;
    }
    
    /* Ajuste para evitar espacio vacío */
    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Tu título personalizado (OPCIONAL - añádelo donde prefieras)
st.sidebar.header("📊 MUGYPS")  # Esto aparecerá BAJO el menú de navegación

# 3. Añadir tu propio título en la posición correcta
st.sidebar.markdown("""
<div style="margin-top: -10px; margin-bottom: 100px;">
    <h1>📊 MUGYPS</h1>
</div>
""", unsafe_allow_html=True)


# === CONFIGURA TU FILE_ID DE GOOGLE DRIVE AQUÍ ===
FILE_ID = "1zqAyIB1BLfCc2uH1v29r-clARHoh2o_s"

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
