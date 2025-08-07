# --- Librerías necesarias ---
import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta, date
from io import BytesIO
import numpy as np
from db_manager import (
    init_db, guardar_asignaciones, guardar_resumen_mensual,
    descargar_bd_desde_drive, subir_bd_a_drive, reset_db
)

# --- Configuración de la página ---
st.set_page_config(page_title="Asignador", layout="wide")
st.title("📋 Asignador de Turnos de Enfermería")

# --- Estados iniciales de la aplicación ---
if "estado" not in st.session_state:
    st.session_state["estado"] = "inicial"
    
# Manejar recarga tras reseteo
if "reset_db_done" in st.session_state and st.session_state["reset_db_done"]:
    st.session_state["reset_db_done"] = False
    st.rerun()

# --- Botones del sidebar ---
# Botón para reiniciar solo la interfaz
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reiniciar aplicación"):
    for k in list(st.session_state.keys()):
        if k not in ["reset_db_done"]:
            del st.session_state[k]
    st.rerun()
# Botón para resetear
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Resetear base de datos"):
    reset_db()
    st.sidebar.success("✅ Base de datos reiniciada correctamente.")
    st.session_state["reset"] = True
    st.session_state["reset_db_done"] = True


# Configuración de base de datos
FILE_ID = "1zqAyIB1BLfCc2uH1v29r-clARHoh2o_s"
descargar_bd_desde_drive(FILE_ID)
init_db()

# Parámetros base
SHIFT_HOURS = {"Mañana": 7.5, "Tarde": 7.5, "Noche": 10}
BASE_MAX_HOURS = {"Mañana": 1642.5, "Tarde": 1642.5, "Noche": 1470}
BASE_MAX_JORNADAS = {"Mañana": 219, "Tarde": 219, "Noche": 147}
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
turnos = ["Mañana", "Tarde", "Noche"]


# --- Funciones auxiliares ---
def parse_dates(cell):
    if pd.isna(cell): return []
    try: return [d.strip() for d in ast.literal_eval(str(cell))]
    except: return [d.strip() for d in str(cell).split(',')]

def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl", date_format="DD/MM/YYYY") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def generar_resumen(df):
    df = df.copy()
    df["Año"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month
    resumen = df.groupby(
        ["ID_Enfermera", "Unidad", "Turno", "Jornada", "Año", "Mes"],
        as_index=False
    ).agg(
        Horas_Asignadas=("Horas_Acumuladas", "sum"),
        Jornadas_Asignadas=("Fecha", "count")
    ).rename(columns={
        "ID_Enfermera": "ID",
        "Fecha": "Jornadas_Asignadas",
        "Horas_Acumuladas": "Horas_Asignadas"
        })
    return resumen

# Subida plantilla de personal
st.subheader("📂  Suba la plantilla de personal")
file_staff = st.file_uploader("Plantilla de personal (.xlsx)", type=["xlsx"])

if not file_staff:
    st.info("🛈 Por favor, suba una plantilla de personal para continuar con la planificación.")
    st.stop()

# Carga plantilla
staff = pd.read_excel(file_staff)
staff.columns = staff.columns.str.strip()
staff["Fechas_No_Disponibilidad"] = staff["Fechas_No_Disponibilidad"].apply(parse_dates)
st.session_state["staff"] = staff  # ✅ IMPORTANTE

# --- Cálculo de horas y jornadas permitidas ---
staff_max_hours = {
    row.ID: BASE_MAX_HOURS[row.Turno_Contrato] * (0.8 if row.Jornada == "Parcial" else 1)
    for _, row in staff.iterrows()
}
staff_max_jornadas = {
     row.ID: BASE_MAX_JORNADAS[row.Turno_Contrato] * (0.8 if row.Jornada == "Parcial" else 1)
     for _, row in staff.iterrows()
 }

st.subheader("👩‍⚕️ Personal cargado")
st.dataframe(staff)

# Selector de método de demanda (página principal)
metodo = st.selectbox("📈 Selecciona el método para ingresar la demanda:", ["Generar manualmente","Desde Excel"])
demand = None

if metodo == "Desde Excel":
    st.subheader("📂 Subir archivo de demanda desde Excel")
    file_demand = st.file_uploader("Demanda de turnos (.xlsx)", type=["xlsx"], key="file_demand_excel")
    if file_demand:
        demand = pd.read_excel(file_demand)
        demand.columns = demand.columns.str.strip()
        st.success("✅ Demanda cargada desde Excel")
        st.dataframe(demand)
        # ✅ Añadir esta línea:
        st.session_state["demand"] = demand
        st.session_state["estado"] = "demanda_generada"
    else:
        st.info("🛈 Por favor, seleccione un archivo Excel con la demanda.")
            
elif metodo == "Generar manualmente":
    st.subheader("⚙️ Generador de Demanda Manual")
    unidad = st.selectbox("Unidad Hospitalaria", ["Medicina Interna", "UCI", "Urgencias", "Oncología", "Quirófano"])
    col1, col2 = st.columns(2)
    fecha_inicio = col1.date_input("Fecha de inicio", value=date(2025, 1, 1))
    fecha_fin = col2.date_input("Fecha de fin", value=date(2025, 1, 31))

    if fecha_fin <= fecha_inicio:
        st.warning("⚠️ La fecha fin debe ser posterior a la fecha inicio.")
        st.stop()

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
    st.session_state['demand'] = demand
    st.session_state['estado'] = 'demanda_generada'



# --- Asignación de turnos (modo simulado aleatorio) ---
if st.session_state.get("estado") == "demanda_generada" and "demand" in st.session_state and "staff" in st.session_state:
    st.subheader("🔄 Asignar turnos automáticamente")

    if st.button("⚙️ Ejecutar asignación"):
        demand = st.session_state["demand"].copy()
        staff = st.session_state["staff"].copy()
        asignaciones = []
        st.write("📋 Demand columnas:", demand.columns.tolist())
        st.write("📊 Primeras filas:", demand.head())


        for _, fila in demand.iterrows():
            if demand.empty:
                st.error("❌ La demanda está vacía. Revisa el origen.")
                st.stop()
            try:
                fecha = fila["Fecha"]
                unidad = fila["Unidad"]
                turno = fila["Turno"]
                requerido = int(fila["Personal_Requerido"])
            except KeyError as e:
                st.error(f"❌ Falta la columna requerida en la demanda: {e}")
                st.stop()
           
            if requerido <= 0:
                continue

            if len(staff) == 0:
                st.error("❌ No hay personal disponible en la plantilla.")
                st.stop()

            asignados = staff.sample(n=min(requerido, len(staff)), replace=False)

            for _, enfermera in asignados.iterrows():
                asignaciones.append({
                    "Fecha": fecha,
                    "ID_Enfermera": enfermera["ID"],
                    "Unidad": unidad,
                    "Turno": turno,
                    "Jornada": enfermera["Jornada"],
                    "Horas_Acumuladas": SHIFT_HOURS[turno]
                })

        df_asignacion = pd.DataFrame(asignaciones)
        if df_asignacion.empty:
            st.error("❌ No se pudieron generar asignaciones. Verifica los datos de plantilla y demanda.")
            st.stop()

        
        st.session_state["df_assign"] = df_asignacion
        st.session_state["estado"] = "asignado"
        #st.rerun()

# --- Visualización y aprobación ---
if st.session_state.get("estado") == "asignado" and "df_assign" in st.session_state:
    st.write("✅ Estado actual:", st.session_state.get("estado"))
    st.write("📋 df_assign:", st.session_state.get("df_assign").head())

    st.subheader("📝 Asignación sugerida")
    st.dataframe(st.session_state["df_assign"])

    col1, col2 = st.columns(2)
    if col1.button("✅ Aprobar asignación"):
        try:
            df_assign = st.session_state["df_assign"].copy()
            df_assign["Fecha"] = pd.to_datetime(df_assign["Fecha"], format="%Y-%m-%d", errors="raise")
            #df_assign["Fecha"] = pd.to_datetime(df_assign["Fecha"], dayfirst=True, errors='coerce')
            if df_assign["Fecha"].isna().any():
                    st.error("❌ Fechas inválidas en la asignación.")
                    st.stop()

            guardar_asignaciones(df_assign)
            resumen = generar_resumen(df_assign)  # Función separada para claridad
            guardar_resumen_mensual(resumen)
            subir_bd_a_drive(FILE_ID)

            # Actualizar estado SIN rerun
            #df_assign["Fecha"] = df_assign["Fecha"].dt.strftime("%d/%m/%Y")
            #st.session_state["df_assign"] = df_assign
            #st.session_state["df_assign"] = df_assign.copy()
            st.session_state["estado"] = "aprobado"
            st.session_state["resumen_mensual"] = resumen
            st.success("✅ Asignación aprobada y datos guardados.")
            st.write("🧭 Estado actual:", st.session_state.get("estado"))
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error durante aprobación: {e}")
            #st.stop()  # Detener ejecución si hay errores

    if col2.button("🔁 Volver a generar asignación"):
        import time
        np.random.seed(int(time.time()))  # Nueva semilla cada vez
        st.session_state["estado"] = "demanda_generada"
        st.experimental_rerun()

# --- Descarga final ---
#if st.session_state.get("estado") == "aprobado" and "df_assign" in st.session_state and "resumen_mensual" in st.session_state:
if st.session_state.get("estado") == "aprobado":
    st.subheader("📄 Asignación final")
    # Asegurar que los datos existen
    if "df_assign" not in st.session_state or "resumen_mensual" not in st.session_state:
        st.error("❌ Datos no encontrados. Vuelve a generar la asignación.")
        st.stop()

    # Mostrar datos
    st.dataframe(st.session_state["df_assign"])
    st.dataframe(st.session_state["resumen_mensual"])

    # Botones de descarga
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Descargar asignación",
            data=to_excel_bytes(st.session_state["df_assign"]),
            file_name=f"Asignacion_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
    with col2:
        st.download_button(
            "⬇️ Descargar resumen",
            data=to_excel_bytes(st.session_state["resumen_mensual"]),
            file_name=f"Resumen_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )

