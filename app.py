import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta, date
from io import BytesIO

from db_manager import (
    init_db, cargar_horas, guardar_horas, guardar_asignaciones,
    cargar_asignaciones, descargar_bd_desde_drive, subir_bd_a_drive
)

# === CONFIGURA TU FILE_ID DE GOOGLE DRIVE AQUÍ ===
FILE_ID = "1zqAyIB1BLfCc2uH1v29r-clARHoh2o_s"

# Sincronizar base de datos
descargar_bd_desde_drive(FILE_ID)
init_db()

st.set_page_config(page_title="Herramienta de planificación de turnos", layout="wide")
st.title("🩺 Planificador de Turnos de Enfermería")

st.markdown("""
Este formulario permite planificar automáticamente los turnos de enfermería para un rango de fechas personalizado.
1 Pestaña Asignador
2. Pestaña Generador de demanda
3. Pestaña Visualización turnos

""")

# Guardar en Drive después de confirmación
if st.session_state.get("asignacion_completada"):
    if st.radio("¿Deseas guardar esta planificación en Drive?", ["No", "Sí"], index=0) == "Sí":
        subir_bd_a_drive(FILE_ID)
        st.success("📤 Base de datos subida a Google Drive.")
