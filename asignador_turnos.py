import streamlit as st
import pandas as pd
import ast

st.set_page_config(page_title="Asignador de Turnos de Enfermería", layout="wide")
st.title("🚀 Asignador Automático de Turnos para Supervisoras")

st.markdown("""
Esta herramienta permite asignar turnos de enfermería de forma automática a partir de:
- Una plantilla de **enfermeras** con información de experiencia, jornada y disponibilidad.
- Una tabla de **demanda** de turnos por día, unidad y franja horaria.
""")

# Subida de archivos
st.sidebar.header("1. Subir archivos")
enfermeras_file = st.sidebar.file_uploader("Plantilla de enfermeras (.xlsx)", type=["xlsx"])
demanda_file = st.sidebar.file_uploader("Demanda de turnos (.xlsx)", type=["xlsx"])

if enfermeras_file and demanda_file:
    enfermeras = pd.read_excel(enfermeras_file)
    demanda = pd.read_excel(demanda_file)

    # Conversión de cadena a lista
    enfermeras["Días_Indisponibles"] = enfermeras["Días_Indisponibles"].apply(lambda x: ast.literal_eval(str(x)))

    # Mostrar tablas originales
    st.subheader("📄 Enfermeras cargadas")
    st.dataframe(enfermeras)

    st.subheader("📅 Demanda de turnos")
    st.dataframe(demanda)

    # Inicializar asignaciones
    st.sidebar.header("2. Ejecutar asignación")
    if st.sidebar.button("Asignar turnos"):
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
            candidatas = candidatas.sort_values(by=["Asignaciones", "Experiencia_Años"], ascending=[True, False])

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
        st.success("👍 Turnos asignados correctamente")
        st.subheader("📆 Planilla generada")
        st.dataframe(df_asignaciones)

        # Descargar resultado
        st.download_button(
            label="📂 Descargar planilla en Excel",
            data=df_asignaciones.to_excel(index=False, engine='openpyxl'),
            file_name="Asignaciones_Turnos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("🔄 Esperando que subas los dos archivos de entrada.")
