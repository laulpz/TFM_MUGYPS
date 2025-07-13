import streamlit as st
from generador_demanda import generar_demanda_interactiva
from asignador import ejecutar_asignador

st.set_page_config(page_title="Planificador de Turnos SERMAS", layout="wide")
st.title("🩺 Planificador de Turnos de Enfermería – SERMAS")

tab1, tab2 = st.tabs(["📆 Generar demanda", "🧠 Asignar turnos"])

with tab1:
    generar_demanda_interactiva()

with tab2:
    ejecutar_asignador()
