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
st.markdown("""
<style>
    /* Solución específica para el menú superior de navegación */
    [data-testid="stSidebarUserContent"] > div:first-child > div:first-child > div:first-child {
        display: none !important;
    }
    
    /* Opcional: Añadir espacio superior si queda vacío */
    [data-testid="stSidebarUserContent"] {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# 3. Añadir tu propio título en la posición correcta
st.sidebar.markdown("""
<div style="margin-top: -50px; margin-bottom: 30px;">
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
