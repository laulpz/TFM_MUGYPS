
import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta, date
from io import BytesIO
from db_manager import init_db, cargar_horas, guardar_horas, guardar_asignaciones

st.set_page_config(page_title="Asignador único de Turnos – SERMAS", layout="wide")
st.title("🩺 Planificador de Turnos de Enfermería (SERMAS)")

init_db()  # Inicializar base de datos

st.markdown("""
Este formulario permite planificar automáticamente los turnos de enfermería para un rango de fechas personalizado.

1. Introduce la demanda semanal por turnos.
2. Elige el rango de fechas.
3. Sube el archivo Excel de plantilla de personal.
4. Ejecuta la asignación.
""")

# Inicializar estados
if "asignacion_completada" not in st.session_state:
    st.session_state["asignacion_completada"] = False
    st.session_state["df_assign"] = None
    st.session_state["df_uncov"] = None
    st.session_state["resumen_horas"] = None

# ───────────────────────────── Demanda semanal ─────────────────────────────
st.subheader("📆 Configura la demanda semanal por turnos")
unidad_seleccionada = st.selectbox("Selecciona la unidad hospitalaria", ["Medicina Interna", "UCI", "Urgencias", "Oncología"])
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
turnos = ["Mañana", "Tarde", "Noche"]
demanda_por_dia = {}

for dia in dias_semana:
    st.markdown(f"**{dia}**")
    cols = st.columns(3)
    demanda_por_dia[dia] = {}
    valor_default = 10 if dia in dias_semana[:5] else 8  # 10 entre semana, 8 fin de semana
    for i, turno in enumerate(turnos):
        demanda_por_dia[dia][turno] = cols[i].number_input(
            label=f"{turno}", min_value=0, max_value=20, value=valor_default, key=f"{dia}_{turno}"
        )

# ───────────────────────────── Rango de fechas ─────────────────────────────
st.markdown("### Selecciona rango de fechas")
col1, col2 = st.columns(2)
fecha_inicio = col1.date_input("Fecha inicio planificación", value=date(2025, 1, 1))
fecha_fin = col2.date_input("Fecha fin planificación", value=date(2025, 1, 31))

if fecha_fin <= fecha_inicio:
    st.warning("⚠️ La fecha fin debe ser posterior a la fecha inicio.")
    st.stop()

# ───────────────────────────── Subida plantilla ─────────────────────────────
st.sidebar.header("📂 Sube un Excel plantilla de personal")
file_staff = st.sidebar.file_uploader("El archivo debe contener las siguientes columnas: ID, Unidad_Asignada. Jornada ", type=["xlsx"])

# ───────────────────────────── Asignación ─────────────────────────────
if file_staff and st.button("🚀 Ejecutar asignación"):
    SHIFT_HOURS = {"Mañana": 7, "Tarde": 7, "Noche": 10}
    MAX_HOURS = {"Mañana": 1667.5, "Tarde": 1667.5, "Noche": 1490}

    staff = pd.read_excel(file_staff)
    staff.columns = staff.columns.str.strip()

    def parse_dates(cell):
        if pd.isna(cell): return []
        try: return [d.strip() for d in ast.literal_eval(str(cell))]
        except: return [d.strip() for d in str(cell).split(',')]

    staff["Fechas_No_Disponibilidad"] = staff["Fechas_No_Disponibilidad"].apply(parse_dates)
    st.subheader("👩‍⚕️ Personal cargado")
    st.dataframe(staff)

    start_date = datetime.combine(fecha_inicio, datetime.min.time())
    end_date = datetime.combine(fecha_fin, datetime.min.time())
    fechas = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    demanda = []
    for fecha in fechas:
        dia_castellano = dias_semana[fecha.weekday()]
        for turno in turnos:
            demanda.append({
                "Fecha": fecha.strftime("%Y-%m-%d"),
                "Unidad": unidad_seleccionada,
                "Turno": turno,
                "Personal_Requerido": demanda_por_dia[dia_castellano][turno]
            })
    demand = pd.DataFrame(demanda)

    df_prev = cargar_horas()
    staff_hours = dict(zip(df_prev["ID"], df_prev["Horas_Acumuladas"])) if not df_prev.empty else {row.ID: 0 for _, row in staff.iterrows()}
    staff_dates = {row.ID: [] for _, row in staff.iterrows()}
    assignments, uncovered = [], []
    demand_sorted = demand.sort_values(by="Fecha")

    for _, dem in demand_sorted.iterrows():
        fecha, unidad, turno, req = dem["Fecha"], dem["Unidad"], dem["Turno"], dem["Personal_Requerido"]
        assigned_count = 0
        cands = staff[(staff["Unidad_Asignada"] == unidad) & (staff["Turno_Contrato"] == turno) & (~staff["Fechas_No_Disponibilidad"].apply(lambda lst: fecha in lst))].copy()
        if not cands.empty:
            cands["Horas_Asignadas"] = cands["ID"].map(staff_hours)
            def consecutive_ok(nurse_id):
                fechas = staff_dates[nurse_id]
                if not fechas: return True
                last_date = max(fechas)
                if (datetime.strptime(fecha, "%Y-%m-%d") - datetime.strptime(last_date, "%Y-%m-%d")).days == 1:
                    consec, check_date = 1, datetime.strptime(last_date, "%Y-%m-%d")
                    while True:
                        check_date -= timedelta(days=1)
                        if check_date.strftime("%Y-%m-%d") in fechas:
                            consec += 1
                            if consec >= 8: return False
                        else: break
                return True
            cands = cands[cands["ID"].apply(consecutive_ok)]
            cands = cands[cands.apply(lambda row: row.Horas_Asignadas + SHIFT_HOURS[turno] <= MAX_HOURS[row.Turno_Contrato], axis=1)]
            cands = cands.sort_values(by="Horas_Asignadas")
        if not cands.empty:
            for _, cand in cands.iterrows():
                if assigned_count >= req: break
                assignments.append({
                    "Fecha": fecha,
                    "Unidad": unidad,
                    "Turno": turno,
                    "ID_Enfermera": cand.ID,
                    "Jornada": cand.Jornada,
                    "Horas_Acumuladas": staff_hours[cand.ID] + SHIFT_HOURS[turno]
                })
                staff_hours[cand.ID] += SHIFT_HOURS[turno]
                staff_dates[cand.ID].append(fecha)
                assigned_count += 1
        if assigned_count < req:
            uncovered.append({"Fecha": fecha, "Unidad": unidad, "Turno": turno, "Faltan": req - assigned_count})

    df_assign = pd.DataFrame(assignments)
    df_uncov = pd.DataFrame(uncovered) if uncovered else None
    resumen_horas = pd.DataFrame([{"ID": id_, "Turno_Contrato": staff.loc[staff.ID == id_, "Turno_Contrato"].values[0],
                                   "Horas_Acumuladas": horas} for id_, horas in staff_hours.items()])

    if not df_prev.empty:
        resumen_horas = pd.concat([df_prev, resumen_horas]).groupby(["ID", "Turno_Contrato"], as_index=False).Horas_Acumuladas.sum()

    # guardar_horas y guardar_asignaciones solo se ejecutan si el usuario aprueba
# Esto se maneja más abajo tras la aprobación

    st.session_state["asignacion_completada"] = True
    st.session_state["df_assign"] = df_assign
    st.session_state["df_uncov"] = df_uncov
    st.session_state["resumen_horas"] = resumen_horas

# Mostrar resultados si hay asignación previa
if st.session_state["asignacion_completada"]:
    st.success("✅ Asignación completada")
    st.dataframe(st.session_state["df_assign"])

    def to_excel_bytes(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button("⬇️ Descargar planilla asignada", data=to_excel_bytes(st.session_state["df_assign"]),
                       file_name="Planilla_Asignada.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if st.session_state["df_uncov"] is not None:
        st.subheader("⚠️ Turnos sin cubrir")
        st.dataframe(st.session_state["df_uncov"])
        st.download_button("⬇️ Descargar turnos sin cubrir", data=to_excel_bytes(st.session_state["df_uncov"]),
                           file_name="Turnos_Sin_Cubrir.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if st.button("🔄 Reiniciar aplicación"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
