import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta

st.set_page_config(page_title="Asignador de Turnos de Enfermería – Criterios SERMAS", layout="wide")
st.title("🩺 Asignador Automático de Turnos (SERMAS)")

st.markdown("""
### Instrucciones
1. **Suba la plantilla de personal** (`.xlsx`) con las columnas:
   - `ID` (código de empleado)
   - `Unidad_Asignada`
   - `Jornada` (`Completa`/`Parcial`)
   - `Turno_Contrato` (`Mañana`, `Tarde` o `Noche`)
   - `Fechas_No_Disponibilidad` (lista `YYYY-MM-DD` separadas por comas)
2. **Suba la demanda de turnos** (`.xlsx`) con las columnas:
   - `Fecha`, `Unidad`, `Turno` (`Mañana`/`Tarde`/`Noche`), `Personal_Requerido`
3. Pulse **Asignar turnos**. La herramienta:
   - Respeta las **8 jornadas consecutivas** máximas.
   - Controla el **límite anual de horas** (1 667,5 h diurnas; 1 490 h nocturnas).
   - Ajusta asignaciones al **Turno_Contrato** y a las **fechas de indisponibilidad**.
4. Descargue la planilla generada y, si hubiera, el listado de turnos sin cubrir.
""")

# ─────────────────────────  Configuraciones generales  ──────────────────────────
SHIFT_HOURS = {"Mañana": 7, "Tarde": 7, "Noche": 10}
MAX_HOURS = {"Mañana": 1667.5, "Tarde": 1667.5, "Noche": 1490}

# ─────────────────────────────  Carga de datos  ────────────────────────────────
st.sidebar.header("📂 Suba los archivos de entrada")
file_staff = st.sidebar.file_uploader("Plantilla de personal (.xlsx)", type=["xlsx"])
file_demand = st.sidebar.file_uploader("Demanda de turnos (.xlsx)", type=["xlsx"])

if file_staff and file_demand:
    staff = pd.read_excel(file_staff)
    demand = pd.read_excel(file_demand)

    # Limpiar espacios extra en nombres de columna
    staff.columns = staff.columns.str.strip()
    demand.columns = demand.columns.str.strip()

    # Limpieza: convertir Fechas_No_Disponibilidad a lista
    def parse_dates(cell):
        if pd.isna(cell):
            return []
        try:
            return [d.strip() for d in ast.literal_eval(str(cell))]
        except Exception:
            return [d.strip() for d in str(cell).split(',')]

    staff["Fechas_No_Disponibilidad"] = staff["Fechas_No_Disponibilidad"].apply(parse_dates)

    st.subheader("👩‍⚕️ Personal cargado")
    st.dataframe(staff)
    st.subheader("📆 Demanda de turnos")
    st.dataframe(demand)

    # ───────────────────────  Motor de asignación  ────────────────────────────
    st.sidebar.header("⚙️ Ejecutar asignación")
    if st.sidebar.button("🚀 Asignar turnos"):
        staff_hours = {row.ID: 0 for _, row in staff.iterrows()}
        staff_dates = {row.ID: [] for _, row in staff.iterrows()}
        assignments, uncovered = [], []

        demand_sorted = demand.sort_values(by="Fecha")

        for _, dem in demand_sorted.iterrows():
            fecha = dem["Fecha"]
            unidad = dem["Unidad"]
            turno = dem["Turno"]
            req = dem["Personal_Requerido"]
            assigned_count = 0

            # Candidatas iniciales
            cands = staff[
                (staff["Unidad_Asignada"] == unidad) &
                (staff["Turno_Contrato"] == turno) &
                (~staff["Fechas_No_Disponibilidad"].apply(lambda lst: fecha in lst))
            ].copy()

            if not cands.empty:
                # Añadir horas acumuladas
                cands["Horas_Asignadas"] = cands["ID"].map(staff_hours)

                # Funciones de validación
                def consecutive_ok(nurse_id):
                    fechas = staff_dates[nurse_id]
                    if not fechas:
                        return True
                    last_date = max(fechas)
                    if (datetime.strptime(fecha, "%Y-%m-%d") - datetime.strptime(last_date, "%Y-%m-%d")).days == 1:
                        consec = 1
                        check_date = datetime.strptime(last_date, "%Y-%m-%d")
                        while True:
                            check_date -= timedelta(days=1)
                            if check_date.strftime("%Y-%m-%d") in fechas:
                                consec += 1
                                if consec >= 8:
                                    return False
                            else:
                                break
                    return True

                cands = cands[cands["ID"].apply(consecutive_ok)]

                def hours_ok(row):
                    return row.Horas_Asignadas + SHIFT_HOURS[turno] <= MAX_HOURS[row.Turno_Contrato]

                cands = cands[cands.apply(hours_ok, axis=1)]
                cands = cands.sort_values(by="Horas_Asignadas")

            # Asignar si hay candidatas disponibles
            if not cands.empty:
                for _, cand in cands.iterrows():
                    if assigned_count >= req:
                        break
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

            # Registrar turnos sin cubrir
            if assigned_count < req:
                uncovered.append({"Fecha": fecha, "Unidad": unidad, "Turno": turno, "Faltan": req - assigned_count})

        # ──────────────────────────  Resultados  ──────────────────────────────
        df_assign = pd.DataFrame(assignments)
        st.success("✅ Asignación completada")
        st.subheader("📋 Planilla generada")
        st.dataframe(df_assign)

        st.download_button(
            label="⬇️ Descargar planilla (Excel)",
            data=df_assign.to_excel(index=False, engine='openpyxl'),
            file_name="Planilla_Asignada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        if uncovered:
            df_uncov = pd.DataFrame(uncovered)
            st.subheader("⚠️ Turnos sin cubrir")
            st.dataframe(df_uncov)
            st.download_button(
                label="⬇️ Descargar turnos sin cubrir",
                data=df_uncov.to_excel(index=False, engine='openpyxl'),
                file_name="Turnos_Sin_Cubrir.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("🔄 Por favor, suba los dos archivos (personal y demanda) para comenzar.")

