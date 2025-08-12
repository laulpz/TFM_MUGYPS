import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

def generar_demanda_interactiva():
    st.markdown("""
    ⚙️ Este módulo permite crear automáticamente la demanda de turnos para una unidad durante el rango de fechas seleccionado por el usuario.
    
    1. Selecciona la unidad que quieres planificar.
    2. Define cuántas enfermeras necesitas por turno para cada día de la semana.
    3. Descarga el Excel para usarlo en la herramienta o para guardar y analizar ese archivo posteriormente.
    """)
    
    unidad_seleccionada = st.selectbox("Selecciona la unidad hospitalaria", [
        "Medicina Interna", "UCI", "Urgencias", "Oncología", "Quirófano"
    ])

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    turnos = ["Mañana", "Tarde", "Noche"]
    
    #Aviso rango de fechas erróneo
    if fecha_fin <= fecha_inicio:
        st.warning("⚠️ La fecha fin debe ser posterior a la fecha inicio.")
        st.stop()
    
    st.markdown("### Configuración de turnos por día")
    demanda_por_dia = {}

    for dia in dias_semana:
        st.markdown(f"**{dia}**")
        cols = st.columns(3)
        demanda_por_dia[dia] = {}
        valor_default = 8 if dia in dias_semana[:5] else 4
        for i, turno in enumerate(turnos):
            demanda_por_dia[dia][turno] = cols[i].number_input(
                label=f"{turno}", min_value=0, max_value=20, value=valor_default, key=f"{dia}_{turno}"
            )

    if st.button("📄 Generar demanda"):
        col1, col2 = st.columns(2)
        fecha_inicio = col1.date_input("Fecha de inicio", value=date(2025, 1, 1))
        fecha_fin = col2.date_input("Fecha de fin", value=date(2025, 1, 31))
        fechas = [fecha_inicio + timedelta(days=i) for i in range((fecha_fin - fecha_inicio).days + 1)]
        #start_date = datetime(2025, 8, 1)
        #fechas = [start_date + timedelta(days=i) for i in range(365)]

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

        df_demanda = pd.DataFrame(demanda)

        def to_excel_bytes(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()

        st.success("✅ Demanda generada correctamente.")
        st.dataframe(df_demanda.head(20))

        st.download_button(
            label="⬇️ Descargar Excel de demanda",
            data=to_excel_bytes(df_demanda),
            file_name=f"Demanda_{unidad_seleccionada}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
