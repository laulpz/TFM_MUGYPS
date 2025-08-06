# --- Librerías necesarias ---
import streamlit as st
import pandas as pd
import ast
import time
from datetime import datetime, timedelta, date
from io import BytesIO
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

st.sidebar.markdown(f"🧪 Estado actual: `{st.session_state.get('estado', 'no definido')}`")
    
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
        {"Fecha": fecha.strftime("%Y-%m-%d"), "Unidad": unidad, "Turno": turno, "Personal_Requerido": demanda_por_dia[dias_semana[fecha.weekday()]][turno]}
        for fecha in fechas for turno in turnos
    ]
    demand = pd.DataFrame(demanda)
    st.session_state['demand'] = demand
    st.session_state['estado'] = 'demanda_generada'

# --- Sección de asignación ---
if st.session_state.get("estado") == "demanda_generada":
    st.subheader("🔄 Asignar turnos automáticamente")

    if st.button("🧠 Ejecutar asignación"):
        demand = st.session_state["demand"].copy()
        staff_ids = staff.ID.tolist()
        asignaciones = []

        for _, fila in demand.iterrows():
            fecha, unidad, turno, requerido = fila["Fecha"], fila["Unidad"], fila["Turno"], fila["Personal_Requerido"]
            asignados = staff.sample(n=min(requerido, len(staff)), replace=False)

            for _, enfermera in asignados.iterrows():
                asignaciones.append({
                    "Fecha": fecha,
                    "ID_Enfermera": enfermera.ID,
                    "Nombre": enfermera.Nombre,
                    "Unidad": unidad,
                    "Turno": turno,
                    "Jornada": enfermera.Jornada,
                    "Horas_Acumuladas": SHIFT_HOURS[turno]
                })

        df_asignacion = pd.DataFrame(asignaciones)
        st.session_state["df_assign"] = df_asignacion
        st.session_state["estado"] = "asignado"
        st.rerun()

# --- Visualización y aprobación ---
if st.session_state.get("estado") == "asignado":
    st.subheader("📝 Asignación sugerida")
    st.dataframe(st.session_state["df_assign"])

    col1, col2 = st.columns(2)
    if col1.button("✅ Aprobar asignación"):
        try:
            df_assign = st.session_state["df_assign"].copy()
            df_assign["Fecha"] = pd.to_datetime(df_assign["Fecha"], dayfirst=True, errors='coerce')
            if df_assign["Fecha"].isna().any():
                st.error("❌ Fechas inválidas en la asignación.")
                st.stop()

            df_assign["Año"] = df_assign["Fecha"].dt.year
            df_assign["Mes"] = df_assign["Fecha"].dt.month

            resumen = df_assign.groupby(
                ["ID_Enfermera", "Unidad", "Turno", "Jornada", "Año", "Mes"],
                as_index=False
            ).agg({
                "Horas_Acumuladas": "sum",
                "Fecha": "count"
            }).rename(columns={
                "ID_Enfermera": "ID",
                "Fecha": "Jornadas_Asignadas",
                "Horas_Acumuladas": "Horas_Asignadas"
            })

            guardar_asignaciones(df_assign)
            guardar_resumen_mensual(resumen)
            subir_bd_a_drive(FILE_ID)

            df_assign["Fecha"] = df_assign["Fecha"].dt.strftime("%d/%m/%Y")
            st.session_state["df_assign"] = df_assign
            st.session_state["resumen_mensual"] = resumen
            st.session_state["estado"] = "aprobado"
            st.success("✅ Asignación aprobada y datos guardados.")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error durante aprobación: {e}")

    if col2.button("🔁 Volver a generar asignación"):
        del st.session_state["df_assign"]
        st.session_state["estado"] = "demanda_generada"
        st.rerun()

# --- Descarga final ---
if st.session_state.get("estado") == "aprobado":
    st.subheader("📄 Asignación final")
    st.dataframe(st.session_state["df_assign"])

    st.subheader("📊 Resumen mensual")
    st.dataframe(st.session_state["resumen_mensual"])

    st.download_button(
        "⬇️ Descargar planilla asignada",
        data=to_excel_bytes(st.session_state["df_assign"]),
        file_name="Planilla_Asignada.xlsx"
    )

    st.download_button(
        "⬇️ Descargar resumen mensual",
        data=to_excel_bytes(st.session_state["resumen_mensual"]),
        file_name="Resumen_Mensual.xlsx"
    )




        

    
                df_vista = df_assign.copy()
                df_vista["Fecha"] = df_vista["Fecha"].dt.strftime("%d/%m/%Y")
    
                st.session_state["df_assign"] = df_vista
                st.session_state["resumen_mensual"] = resumen_mensual
                st.session_state["estado"] = "aprobado"
    
                st.success("✅ Asignación aprobada y base de datos actualizada.")
                st.rerun()
    
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")
                st.stop()
    

    if col2.button("🔁 Volver a generar asignación"):
        del st.session_state["df_assign"]
        st.session_state["estado"] = "inicial"
        st.rerun()

# --- Sección final: descarga tras aprobación ---
if st.session_state.get("estado") == "aprobado":
    st.success("✅ Asignación aprobada")

    st.subheader("📄 Asignación final")
    st.dataframe(st.session_state["df_assign"])

    st.subheader("📊 Resumen mensual")
    st.dataframe(st.session_state["resumen_mensual"])

    st.download_button(
        "⬇️ Descargar planilla asignada",
        data=to_excel_bytes(st.session_state["df_assign"]),
        file_name="Planilla_Asignada.xlsx"
    )

    st.download_button(
        "⬇️ Descargar resumen mensual",
        data=to_excel_bytes(st.session_state["resumen_mensual"]),
        file_name="Resumen_Mensual.xlsx"
    )


