import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from io import BytesIO
from db_manager import (
    init_db, cargar_horas, guardar_horas, guardar_asignaciones,
    cargar_asignaciones, descargar_bd_desde_drive, subir_bd_a_drive
)

st.set_page_config(  # ← Esto es imprescindible
    page_title="Inicio",  # Título en la pestaña del navegador
    page_icon="🏥",       # Icono
    layout="wide",        # Diseño
    initial_sidebar_state="expanded"  # Sidebar visible
)


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


from PIL import Image  # Opcional para procesamiento adicional

# Ruta a tu imagen (puede ser local o URL)
imagen_path = "images/Imagen_Bienvenida.png"

# Cargar y mostrar imagen
st.image(
    imagen_path,
    width=400,  # Ancho en píxeles (ajustable)
    use_container_width=False,  # Otra opción para ajuste automático
    output_format="auto" 
)
