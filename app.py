import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Asignador único de Turnos – SERMAS", layout="wide")
st.title("🩺 Planificador de Turnos de Enfermería (SERMAS)")

st.markdown("""
Este formulario permite planificar automáticamente los turnos de enfermería para 365 días, sin necesidad de generar archivos intermedios.

1. Introduce la demanda semanal por turnos.
2. Sube el archivo Excel de plantilla de personal.
3. Ejecuta la asignación.
""")

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
    for i, turno in enumerate(turnos):
        demanda_por_dia[dia][turno] = cols[i].number_input(
            label=f"{turno}", min_value=0, max_value=20, value=3, key=f"{dia}_{turno}"
        )

# ───────────────────────────── Subida plantilla ─────────────────────────────
st.sidebar.header("📂 Suba plantilla de personal")
file_staff = st.sidebar.file_uploader("Plantilla de personal (.xlsx)", type=["xlsx"])

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

    # Generar demanda anual
    start_date = datetime(2025, 1, 1)
    fechas = [start_date + timedelta(days=i) for i in range(365)]
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

    staff_hours = {row.ID: 0 for _, row in staff.iterrows()}
    staff_dates = {row.ID: [] for _, row in staff.iterrows()}
    assignments, uncovered = [], []
    demand_sorted = demand.sort_values(by="Fecha")

    for _, dem in demand_sorted.iterrows():
        fecha, unidad, turno, req = dem["Fecha"], dem["Unidad"], dem["Turno"], dem["Personal_Requerido"]
        assigned_count = 0
        cands = staff[(staff["Unidad_Asignada"] == unidad) & (staff["Turno_Contrato"] == turno) &
                      (~staff["Fechas_No_Disponibilidad"].apply(lambda lst: fecha in lst))].copy()

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
                    "Jornada": cand.Jornada
                })
                staff_hours[cand.ID] += SHIFT_HOURS[turno]
                staff_dates[cand.ID].append(fecha)
                assigned_count += 1

        if assigned_count < req:
            uncovered.append({"Fecha": fecha, "Unidad": unidad, "Turno": turno, "Faltan": req - assigned_count})

    df_assign = pd.DataFrame(assignments)
    st.success("✅ Asignación completada")
    st.dataframe(df_assign)

    def to_excel_bytes(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button("⬇️ Descargar planilla asignada", data=to_excel_bytes(df_assign), file_name="Planilla_Asignada.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if uncovered:
        df_uncov = pd.DataFrame(uncovered)
        st.subheader("⚠️ Turnos sin cubrir")
        st.dataframe(df_uncov)
        st.download_button("⬇️ Descargar turnos sin cubrir", data=to_excel_bytes(df_uncov),
                           file_name="Turnos_Sin_Cubrir.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("🔄 Por favor, configure la demanda e introduzca la plantilla de personal para comenzar.")
