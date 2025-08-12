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


import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

# Configuración del canvas
fig, ax = plt.subplots(figsize=(10, 4), facecolor='#0E1117')  # Fondo oscuro como Streamlit
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.axis('off')

# Elementos gráficos
ax.add_patch(Rectangle((0.5, 0.5), 9, 3, fill=True, color='#990000', alpha=0.2))  # Marco

# Texto principal
ax.text(5, 2.5, 'MUGYPS', ha='center', va='center', 
        fontsize=48, color='white', weight='bold', fontfamily='sans-serif')

# Subtítulo
ax.text(5, 1.5, 'Herramienta de análisis geoespacial', ha='center', va='center',
        fontsize=18, color='#9fbdd7', fontfamily='sans-serif')

# Logo/icono
#ax.text(1, 3.2, '📊', ha='center', va='center', fontsize=36)

# Línea decorativa
ax.plot([3, 7], [1.2, 1.2], color='#990000', linewidth=3, alpha=0.7)

# Guardar y mostrar
plt.tight_layout()
st.pyplot(fig)
