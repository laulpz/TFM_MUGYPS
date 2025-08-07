# --- Librerías ---
import streamlit as st
import pandas as pd
import ast
from datetime import datetime, date, timedelta
from io import BytesIO
from db_manager import (
    descargar_bd_desde_drive, 
    guardar_asignaciones, 
    guardar_resumen_mensual,
    subir_bd_a_drive
)

# --- Configuración ---
st.set_page_config(page_title="Asignador de Turnos", layout="wide")
st.title("📋 Asignador de Turnos de Enfermería")

# --- Parámetros ---
SHIFT_HOURS = {"Mañana": 7.5, "Tarde": 7.5, "Noche": 10}
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
turnos = ["Mañana", "Tarde", "Noche"]
FILE_ID = "1zqAyIB1BLfCc2uH1v29r-clARHoh2o_s"  # ID de tu archivo en Drive

# --- Funciones auxiliares ---
def parse_dates(cell):
    """Convierte celdas de fechas no disponibles a lista"""
    if pd.isna(cell): return []
    try: return [d.strip() for d in ast.literal_eval(str(cell))]
    except: return [d.strip() for d in str(cell).split(',')]

def to_excel_bytes(df):
    """Convierte DataFrame a bytes para descarga"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def generar_resumen(asignaciones):
    """Genera resumen mensual de horas (igual que en asignador.py)"""
    df = asignaciones.copy()
    df["Año"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month
    return df.groupby(
        ["ID_Enfermera", "Unidad", "Turno", "Jornada", "Año", "Mes"],
        as_index=False
    ).agg(
        Horas_Asignadas=("Horas_Acumuladas", "sum"),
        Jornadas_Asignadas=("Fecha", "count")
    ).rename(columns={"ID_Enfermera": "ID"})

# --- Inicialización ---
if "estado" not in st.session_state:
    st.session_state.estado = "cargando"
    descargar_bd_desde_drive(FILE_ID)  # Descarga turnos.db desde Drive

# --- Carga de plantilla de personal ---
st.subheader("1️⃣ Cargar plantilla de personal")
file_staff = st.file_uploader("Subir archivo Excel de personal", type=["xlsx"])

if file_staff:
    staff = pd.read_excel(file_staff)
    staff["Fechas_No_Disponibilidad"] = staff["Fechas_No_Disponibilidad"].apply(parse_dates)
    st.session_state.staff = staff
    st.session_state.estado = "cargado"
    st.success("✅ Plantilla cargada correctamente")

# --- Generación de demanda ---
if st.session_state.estado == "cargado":
    st.subheader("2️⃣ Generar demanda")
    metodo = st.radio("Seleccione método:", ["Manual", "Desde Excel"], horizontal=True)
    
    if metodo == "Desde Excel":
        file_demand = st.file_uploader("Subir archivo de demanda", type=["xlsx"])
        if file_demand:
            demanda = pd.read_excel(file_demand)
            st.session_state.demanda = demanda
    else:
        # Generación manual (simplificada)
        unidad = st.selectbox("Unidad Hospitalaria", ["Medicina Interna", "UCI", "Urgencias", "Oncología", "Quirófano"])
        col1, col2 = st.columns(2)
        fecha_inicio = col1.date_input("Fecha de inicio", value=date(2025, 1, 1))
        fecha_fin = col2.date_input("Fecha de fin", value=date(2025, 1, 31))
        
        if fecha_fin > fecha_inicio:
            demanda_por_dia = {}
            for dia in dias_semana:
                st.markdown(f"**{dia}**")
                cols = st.columns(3)
                demanda_por_dia[dia] = {
                    turno: cols[i].number_input(label=f"{turno}", min_value=0, max_value=20, value=3, key=f"{dia}_{turno}")
                    for i, turno in enumerate(turnos)
                }

            fechas = [fecha_inicio + timedelta(days=i) for i in range((fecha_fin - fecha_inicio).days + 1)]
            demanda = [
                {"Fecha": fecha, "Unidad": unidad, "Turno": turno, "Personal_Requerido": demanda_por_dia[dias_semana[fecha.weekday()]][turno]}
                for fecha in fechas for turno in turnos
            ]
            demand = pd.DataFrame(demanda)


# --- Asignación de turnos ---
if st.session_state.get("demanda") is not None:
    st.subheader("3️⃣ Generar asignación")
    if st.button("⚙️ Asignar turnos automáticamente"):
        asignaciones = []
        for _, fila in st.session_state.demanda.iterrows():
            disponibles = st.session_state.staff[
                ~st.session_state.staff["Fechas_No_Disponibilidad"].apply(
                    lambda x: str(fila["Fecha"]) in x
                )
            ]
            asignados = disponibles.sample(min(fila["Personal_Requerido"], len(disponibles)))
            
            for _, enfermera in asignados.iterrows():
                asignaciones.append({
                    "Fecha": fila["Fecha"],
                    "ID_Enfermera": enfermera["ID"],
                    "Turno": fila["Turno"],
                    "Jornada": enfermera["Jornada"],
                    "Horas_Acumuladas": SHIFT_HOURS[fila["Turno"]]
                })
        
        st.session_state.asignaciones = pd.DataFrame(asignaciones)
        st.session_state.estado = "asignado"
        st.rerun()

# --- Aprobación y descarga ---
if st.session_state.estado == "asignado":
    st.subheader("4️⃣ Revisar y aprobar")
    st.dataframe(st.session_state.asignaciones)
    
    if st.button("✅ Aprobar asignación"):
        guardar_asignaciones(st.session_state.asignaciones)
        resumen = generar_resumen(st.session_state.asignaciones)
        guardar_resumen_mensual(resumen)
        subir_bd_a_drive(FILE_ID)
        
        st.session_state.estado = "aprobado"
        st.session_state.resumen = resumen
        st.success("🗄️ Asignación guardada en la base de datos")

if st.session_state.estado == "aprobado":
    st.subheader("5️⃣ Descargar resultados")
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            "⬇️ Descargar asignación completa",
            data=to_excel_bytes(st.session_state.asignaciones),
            file_name=f"asignacion_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
    
    with col2:
        st.download_button(
            "⬇️ Descargar resumen mensual",
            data=to_excel_bytes(st.session_state.resumen),
            file_name=f"resumen_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
