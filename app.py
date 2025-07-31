
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from db_manager import cargar_asignaciones

# Generador de histórico mensual por profesional
df_hist = cargar_asignaciones()
if not df_hist.empty:
    df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"])
    df_hist["Año"] = df_hist["Fecha"].dt.year
    df_hist["Mes"] = df_hist["Fecha"].dt.month
    resumen_mensual = df_hist.groupby(
        ["ID_Enfermera", "Unidad", "Turno", "Año", "Mes"],
        as_index=False
    ).agg({"Horas_Acumuladas": "sum", "Fecha": "count"})
    resumen_mensual = resumen_mensual.rename(
        columns={"ID_Enfermera": "ID", "Fecha": "Jornadas Asignadas", "Horas_Acumuladas": "Horas Asignadas"}
    )

    def to_excel_bytes(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Resumen_Mensual")
        return output.getvalue()

    st.sidebar.download_button(
        label="📤 Descargar histórico mensual",
        data=to_excel_bytes(resumen_mensual),
        file_name="Historico_Mensual_Profesional.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.sidebar.warning("No hay asignaciones previas registradas.")
