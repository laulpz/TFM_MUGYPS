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

# CSS para eliminación completa y reemplazo perfecto
st.markdown("""
<style>
    /* Elimina el texto "app" original SIN dejar rastro */
    [data-testid="stSidebarNav"] + div [data-testid="stVerticalBlock"] > div:first-child {
        display: none !important;
    }
    
    /* Contenedor del nuevo título con posicionamiento absoluto */
    .custom-sidebar-title {
        position: absolute;
        top: 20px;
        left: 20px;
        font-size: 18px;
        font-weight: 600;
        color: inherit;
        z-index: 1000002;
        pointer-events: none;
    }
    
    /* Ajuste del padding superior del sidebar */
    [data-testid="stSidebarUserContent"] {
        padding-top: 50px !important;
    }
</style>
""", unsafe_allow_html=True)

# Añade tu título personalizado (perfectamente alineado)
st.sidebar.markdown('<div class="custom-sidebar-title">📊 MUGYPS</div>', unsafe_allow_html=True)

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
