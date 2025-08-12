import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from io import BytesIO
from db_manager import (
    init_db, cargar_horas, guardar_horas, guardar_asignaciones,
    cargar_asignaciones, descargar_bd_desde_drive, subir_bd_a_drive
)

st.set_page_config(page_title="Inicio", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# === CONFIGURA TU FILE_ID DE GOOGLE DRIVE AQUÍ ===
FILE_ID = "1zqAyIB1BLfCc2uH1v29r-clARHoh2o_s"

# Sincronizar base de datos
descargar_bd_desde_drive(FILE_ID)
init_db()

# Barra lateral personalizada
with st.sidebar:
    st.title("Menú Principal🏥")
    st.markdown("### Menú Principal")
    st.page_link("pages/1_📋 Asignador.py", label="Asignación de Turnos", icon="📋")
    st.page_link("pages/2_📋 Asignador.py", label="Generador de demanda", icon="📋")
    st.page_link("pages/3_📋 Asignador.py", label="Informes", icon="📋")
    # Añade más páginas aquí

st.title("🩺 Planificador de Turnos de Enfermería")

st.markdown("""
¡Bienvend@!
Esta herramienta permite planificar automáticamente los turnos de enfermería para un rango de fechas personalizado. Navega por cada una de las pestañas para aprender más sobre ellas.
1. Pestaña Asignador
2. Pestaña Generador de demanda
3. Pestaña Visualización turnos
""")
