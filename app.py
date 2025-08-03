import streamlit as st
from db_manager import init_db
init_db()

st.set_page_config(page_title="Planificador de Turnos – SERMAS", layout="wide")
st.title("🩺 Planificador de Turnos de Enfermería – SERMAS")
st.markdown("""
Bienvenida al sistema de planificación de turnos de enfermería.

Usa el menú lateral izquierdo para:
- Asignar turnos
- Generar demanda
- Consultar el resumen mensual
""")
