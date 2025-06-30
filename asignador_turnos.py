import streamlit as st
import pandas as pd
import ast

st.set_page_config(page_title="Asignador de Turnos de Enfermería", layout="wide")
st.title("🩺 Asignador Automático de Turnos para Enfermería")

st.markdown("""
Esta herramienta permite a las supervisoras de enfermería:
- Subir datos del personal y demanda de turnos.
- Ejecutar la asignación automática cumpliendo criterios básicos.
- Visualizar y descargar la planilla generada.

**Versión beta para pruebas en hospitales del SERMAS**.
""")

st.sidebar.header("📂 Subir archivos de entrada")
enfermeras_file = st.sidebar.file_uploader("Plantilla de enfermeras (.xlsx)", type=["xlsx"])
demanda_file = st.sidebar.file_uploader("Demanda de turnos (.xlsx)", type=["xlsx"])

if enfermeras_file and demanda_file:
    enfermeras = pd.read_excel(enfermeras_file)
    demanda = pd.read_excel(demanda_file)

    enfermeras["Días_Indisponibles"] = enfermeras["Días_Indisponibles"].apply(lambda x: ast.literal_eval(str(x)))

    st.subheader("👩‍⚕️ Enfermeras cargadas")
    st.dataframe(enfermeras)

    st.subheader("📆 Demanda de turnos")
    st.dataframe(demanda)

    st.sidebar.header("⚙️ Opciones de asignación")
    aplicar_preferencia = st.sidebar.checkbox("Priorizar turno preferido", value=True)
    aplicar_experiencia = st.sidebar.checkbox("Priorizar experiencia en caso de empate", value=True)

    if st.sidebar.button("🚀 Ejecutar asignación"):
        asignaciones = []
        asignaciones_por_enfermera = {eid: 0 for eid in enfermeras["ID"]}

        for _, row in demanda.iterrows():
            fecha = row["Fecha"]
            unidad = row["Unidad"]
            turno = row["Turno"]
            requerido = row["Personal_Requerido"]

            candidatas = enfermeras[
                (enfermeras["Unidad_Asignada"] == unidad) &
                (~enfermeras["Días_Indisponibles"].apply(lambda x: fecha in x))
            ].copy()

            candidatas["Asignaciones"] = candidatas["ID"].map(asignaciones_por_enfermera)

            orden = ["Asignaciones"]
            if aplicar_preferencia:
                candidatas["PrefiereEsteTurno"] = (candidatas["Preferencia_Turno"] == turno).astype(int)
                orden.append("PrefiereEsteTurno")
            if aplicar_experiencia:
                orden.append("Experiencia_Años")

            candidatas = candidatas.sort_values(by=orden, ascending=[True, False] * len(orden))
            seleccionadas = candidatas.head(requerido)

            for _, enf in seleccionadas.iterrows():
                asignaciones.append({
                    "Fecha": fecha,
                    "Unidad": unidad,
                    "Turno": turno,
                    "ID_Enfermera": enf["ID"],
                    "Nombre": enf["Nombre"]
                })
                asignaciones_por_enfermera[enf["ID"]] += 1

        df_asignaciones = pd.DataFrame(asignaciones)
        st.success("✅ Turnos asignados correctamente")
        st.subheader("📋 Planilla generada")
        st.dataframe(df_asignaciones)

        st.download_button(
            label="⬇️ Descargar planilla en Excel",
            data=df_asignaciones.to_excel(index=False, engine='openpyxl'),
            file_name="Asignaciones_Turnos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("🔄 Por favor, sube los dos archivos de entrada para comenzar.")
