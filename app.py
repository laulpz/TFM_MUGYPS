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

# Solución minimalista:
# 1. Ocultar el sidebar automático
st.markdown("""
<style>
    /* Oculta solo el texto */
    [data-testid="stSidebarNav"] span {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# 2. Crear sidebar personalizado desde cero
with st.sidebar:
    st.header("📊 MUGYPS")  # Tu título personalizado
    # Aquí añades tus controles/widgets manualmente
    # Ejemplo:
    # st.selectbox("Menú", options=["Opción 1", "Opción 2"])
    


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
