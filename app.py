import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from io import BytesIO
from db_manager import (
    init_db, cargar_horas, guardar_horas, guardar_asignaciones,
    cargar_asignaciones, descargar_bd_desde_drive, subir_bd_a_drive
)

# SOLUCIÓN DEFINITIVA - Reemplaza "app" manteniendo todo lo demás
st.markdown("""
<style>
    [data-testid="stSidebarUserContent"] > div:first-child > div:first-child > div:first-child {
        visibility: hidden;
        height: 0px;
    }
    [data-testid="stSidebarUserContent"] > div:first-child > div:first-child > div:first-child:after {
        content: "MUGYPS";
        visibility: visible;
        display: block;
        height: auto;
        font-size: 18px;
        font-weight: bold;
        margin-top: -20px;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.header("MUGYPS")


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
