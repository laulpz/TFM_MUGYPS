import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta, date
from io import BytesIO
from db_manager import (
    init_db, guardar_asignaciones, guardar_resumen_mensual,
    descargar_bd_desde_drive, subir_bd_a_drive, reset_db
)

#Definir funciones necesarias
def to_excel_bytes(df):
    #Convierte DataFrame a bytes para descarga en Excel
    if df is None or df.empty:
        return b''  # Retorna bytes vacíos si no hay datos
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def parse_dates(cell):
    """
    Parsea fechas de no disponibilidad en varios formatos a lista de strings 'YYYY-MM-DD'.
    Maneja todos los casos posibles de forma segura.
    """
    def safe_str_convert(value):
        """Conversión segura a string"""
        try:
            return str(value).strip()
        except:
            return ""
    def try_parse_date(date_str):
        """Intenta parsear una fecha en múltiples formatos"""
        date_str = safe_str_convert(date_str)
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None
    # Caso 1: Valor es None, NaN, vacío o cualquier tipo inesperado
    try:
        if pd.isna(cell) or cell is None or not safe_str_convert(cell):
            return []
    except Exception:
        return []
    # Caso 2: Si ya es una lista válida
    if isinstance(cell, list):
        try:
            return sorted(list(set(cell)))  # Eliminar duplicados y ordenar
        except:
            return []
    # Procesamiento principal
    dates = set()
    content = safe_str_convert(cell)
    try:
        # Caso 3: Timestamp de pandas (ej: '2025-04-14 00:00:00')
        if " " in content and "-" in content and ":" in content:
            try:
                date_part = content.split(" ")[0]
                date_obj = datetime.strptime(date_part, "%Y-%m-%d").date()
                return [date_obj.strftime("%Y-%m-%d")]
            except:
                pass
        # Dividir por comas y procesar cada parte
        parts = [part.strip() for part in content.split(",") if part.strip()]
        for part in parts:
            # Manejar rangos (contiene '-')
            if "-" in part:
                range_parts = part.split("-")
                if len(range_parts) == 2:
                    start, end = map(safe_str_convert, range_parts)
                    start_date = try_parse_date(start)
                    end_date = try_parse_date(end)
                    if start_date and end_date:
                        if start_date > end_date:
                            st.warning(f"Rango inválido: {start} > {end}")
                            continue
                        current = start_date
                        while current <= end_date:
                            dates.add(current.strftime("%Y-%m-%d"))
                            current += timedelta(days=1)
                    else:
                        st.warning(f"Formato no reconocido en rango: '{part}'")
                else:
                    st.warning(f"Formato de rango inválido: '{part}'")
            # Fecha individual
            else:
                date_obj = try_parse_date(part)
                if date_obj:
                    dates.add(date_obj.strftime("%Y-%m-%d"))
                else:
                    st.warning(f"Formato de fecha no reconocido: '{part}'")
        return sorted(list(dates))
    except Exception as e:
        st.error(f"Error procesando: '{content}'. Se omitirá esta entrada.")
        return []

def generar_plantilla_ejemplo():
    data = {
        "ID": ["E001", "E002"],
        "Unidad_Asignada": ["UCI", "Urgencias"],
        "Jornada": ["Completa", "Parcial"],
        "Turno_Contrato": ["Mañana", "Tarde"],
        "Fechas_No_Disponibilidad": [
            "01/02/2025-05/02/2025, 20/07/2025",  # Ejemplo combinado
            "15/03/2025"  # Ejemplo simple
        ]
    }
    return pd.DataFrame(data)

#Inicialización de variables
SHIFT_HOURS = {"Mañana": 7.5, "Tarde": 7.5, "Noche": 10}
BASE_MAX_HOURS = {"Mañana": 1642.5, "Tarde": 1642.5, "Noche": 1470}
BASE_MAX_JORNADAS = {"Mañana": 219, "Tarde": 219, "Noche": 147}
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
turnos = ["Mañana", "Tarde", "Noche"]


#Títulos y descripción
st.set_page_config(page_title="Asignador", layout="wide")
st.title("📋Asignador de Turnos")
st.markdown("""
    Instrucciones:
    1. Sube el archivo Excel de plantilla de personal (.xlsx) con las columnas:
       - `ID` (código de empleado)
       - `Unidad_Asignada`
       - `Jornada` (`Completa`/`Parcial`)
       - `Turno_Contrato` (`Mañana`, `Tarde` o `Noche`)
       - `Fechas_No_Disponibilidad` (fechas individuales y/o rangos `dd/mm/AAAA` separadas por comas). 
    2. Crea la demanda de turnos en el rango de fechas de interés de una de las siguientes formas:
        - Sube la demanda de turnos** (`.xlsx`) con las columnas `Fecha`, `Unidad`, `Turno` (`Mañana`/`Tarde`/`Noche`), `Personal_Requerido`
        - Genera la demanda directamente desde la propia aplicación
    3. Ejecuta la asignación. 
    """)

#Carga BBDD
FILE_ID = "1zqAyIB1BLfCc2uH1v29r-clARHoh2o_s"
descargar_bd_desde_drive(FILE_ID)
init_db()

#Comprobar estado para conservar el de la sesión anterior.
if "asignacion_completada" not in st.session_state:
    st.session_state.update({
        "asignacion_completada": False,
        "df_assign": None,
        "file_staff": None,
        "df_uncov": None
    })

if "file_staff" not in st.session_state:
    st.session_state["file_staff"] = None

#Subida plantilla de personal. 10/08 añadido if para st.session_state
st.sidebar.header("1️⃣📂 Sube la plantilla de personal")
file_staff = st.sidebar.file_uploader(
    "Plantilla de personal (.xlsx)",
    type=["xlsx"],
    help="""La columna 'Fechas_No_Disponibilidad' puede contener fechas individuales (20/07/2025), rangos (01/02/2025-10/02/2025) o combinaciones de ambas separadas por comas. Ejemplo: 01/07/2025-15/07/2025, 12/10/2025"""
)

if st.sidebar.download_button(
    label="📥 Ejemplo de plantilla",
    data=to_excel_bytes(generar_plantilla_ejemplo()),
    file_name="Plantilla_Turnos_Ejemplo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=False  # Esto hace el botón más pequeño
):
    pass  # Para que no aparezca "None" en el sidebar

if file_staff:
    st.session_state["file_staff"] = file_staff
    staff = pd.read_excel(file_staff)
    staff.columns = staff.columns.str.strip()

    # Validar columnas requeridas
    required_columns = ["ID", "Unidad_Asignada", "Jornada", "Turno_Contrato", "Fechas_No_Disponibilidad"]
    if not all(col in staff.columns for col in required_columns):
        missing = [col for col in required_columns if col not in staff.columns]
        st.error(f"Faltan columnas requeridas: {', '.join(missing)}")
        st.stop()

    # Limpieza y validación de datos
    staff = staff.dropna(subset=["ID", "Turno_Contrato"])  # Eliminar filas sin ID o Turno
    #Normalización de valores
    staff["Turno_Contrato"] = staff["Turno_Contrato"].astype(str).str.strip().str.capitalize()
    staff["Jornada"] = staff["Jornada"].astype(str).str.strip().str.capitalize()
    
    # Validar valores aceptados
    valid_turnos = ["Mañana", "Tarde", "Noche"]
    invalid_turnos = staff[~staff["Turno_Contrato"].isin(valid_turnos)]
    
    if not invalid_turnos.empty:
        st.warning(f"Se encontraron turnos no válidos: {invalid_turnos['Turno_Contrato'].unique()}")
        staff = staff[staff["Turno_Contrato"].isin(valid_turnos)]  # Filtrar solo turnos válidos
    
    # Procesar fechas
    staff["Fechas_No_Disponibilidad"] = staff["Fechas_No_Disponibilidad"].apply(parse_dates)

    #MOSTRAR EJEMPLO DE PARSING
    sample = staff["Fechas_No_Disponibilidad"].iloc[0] if not staff.empty else []
    st.sidebar.markdown(f"🔍 **Ejemplo de fechas parseadas:**\n`{sample}`")
    #st.info("🛈 Por favor, suba una plantilla de personal para continuar con la planificación.")
    
#Configurar la demanda de turnos
st.sidebar.header("2️⃣📈 Selecciona el Método para ingresar demanda:")
metodo = st.sidebar.selectbox("Generar desde la aplicación se muestra por defecto", ["Desde aplicación","Desde Excel"],
                              help="""El Excel (`.xlsx`) debe contener las columnas `Fecha`, `Unidad`, `Turno` (`Mañana`/`Tarde`/`Noche`), `Personal_Requerido`""")
demand = None
if metodo == "Desde Excel":
    file_demand = st.sidebar.file_uploader("Demanda de turnos (.xlsx)", type=["xlsx"])
    if file_demand:
        demand = pd.read_excel(file_demand)
        demand.columns = demand.columns.str.strip()
        st.subheader("📆 Demanda desde archivo")
        st.dataframe(demand)
elif metodo == "Desde aplicación":
    st.subheader("⚙️ Generador de Demanda")
    unidad = st.selectbox("Selecciona la Unidad Hospitalaria", ["Medicina Interna", "UCI", "Urgencias", "Oncología", "Quirófano"])
    col1, col2 = st.columns(2)
    fecha_inicio = col1.date_input("Fecha de inicio", value=date(2025, 1, 1))
    fecha_fin = col2.date_input("Fecha de fin", value=date(2025, 1, 31))
    fechas = [fecha_inicio + timedelta(days=i) for i in range((fecha_fin - fecha_inicio).days + 1)]
    
    #Aviso rango de fechas erróneo
    if fecha_fin <= fecha_inicio:
        st.warning("⚠️ La fecha fin debe ser posterior a la fecha inicio.")
        st.stop()
        
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
    demanda = []
    for fecha in fechas:
        dia_cast = dias_semana[fecha.weekday()]
        for turno in turnos:
             demanda.append({
                 "Fecha": fecha.isoformat(),
                 "Unidad": unidad,
                 "Turno": turno,
                 "Personal_Requerido": demanda_por_dia[dia_cast][turno]
             })
    demand = pd.DataFrame(demanda)

#Ejecutar asignación
if file_staff is not None and st.button("3️⃣🚀 Ejecutar asignación"):
    TURNOS_VALIDOS = {
    "Mañana": {"horas": 1642.5, "jornadas": 219},
    "Tarde": {"horas": 1642.5, "jornadas": 219},
    "Noche": {"horas": 1470, "jornadas": 147}
    }
    # Modificar la creación de staff_max_hours y staff_max_jornadas
    staff_max_hours = {}
    staff_max_jornadas = {}
    for _, row in staff.iterrows():
        try:
            turno = str(row.Turno_Contrato).strip()
            jornada = str(row.Jornada).strip() if pd.notna(row.Jornada) else "Completa"
        
            # Validar y obtener valores para el turno
            if turno in TURNOS_VALIDOS:
                factor = 0.8 if jornada == "Parcial" else 1
                staff_max_hours[row.ID] = TURNOS_VALIDOS[turno]["horas"] * factor
                staff_max_jornadas[row.ID] = TURNOS_VALIDOS[turno]["jornadas"] * factor
            else:
                st.warning(f"Turno no válido '{turno}' para empleado {row.ID}. Usando valores por defecto.")
                # Valores por defecto (promedio)
                staff_max_hours[row.ID] = 1585 * (0.8 if jornada == "Parcial" else 1)
                staff_max_jornadas[row.ID] = 200 * (0.8 if jornada == "Parcial" else 1)
        except Exception as e:
            st.error(f"Error procesando empleado {row.ID}: {str(e)}")
            # Valores por defecto seguros
            staff_max_hours[row.ID] = 1585 * 0.8  # Asume jornada parcial por seguridad
            staff_max_jornadas[row.ID] = 200 * 0.8
    
    st.markdown("""👩‍⚕️ Personal cargado""")
    st.dataframe(staff)
    #Aquí está obviando las horas anteriores. En código 31/07 algo así: 
    #df_prev = cargar_horas()
    #staff_hours = dict(zip(df_prev["ID"], df_prev["Horas_Acumuladas"])) if not df_prev.empty else {row.ID: 0 for _, row in staff.iterrows()}
    #staff_jornadas = dict.fromkeys(staff["ID"], 0)
    
    staff_hours = {row.ID: 0 for _, row in staff.iterrows()}
    staff_dates = {row.ID: [] for _, row in staff.iterrows()}
    staff_jornadas = {row.ID: 0 for _, row in staff.iterrows()}  # Inicialización adicional para jornadas
    assignments, uncovered = [], []

    if demand is None:
        st.warning("⚠️ No se ha cargado ninguna demanda de turnos.")
        st.stop()

    if not all(col in demand.columns for col in ["Fecha", "Unidad", "Turno", "Personal_Requerido"]):
        st.error("❌ La demanda debe contener las columnas: Fecha, Unidad, Turno, Personal_Requerido")
        st.stop()

    demand_sorted = demand.sort_values(by="Fecha")
    #st.subheader("📆 Demanda generada")
    #st.dataframe(demand)

    for _, dem in demand_sorted.iterrows():
        fecha = dem["Fecha"]
        unidad = dem["Unidad"]
        turno = dem["Turno"]
        req = dem["Personal_Requerido"]
        assigned_count = 0

        cands = staff[
            (staff["Unidad_Asignada"] == unidad) &
            (staff["Turno_Contrato"] == turno) &
            (~staff["Fechas_No_Disponibilidad"].apply(lambda lst: fecha in lst))
        ].copy()

        if not cands.empty:
            cands["Horas_Asignadas"] = cands["ID"].map(staff_hours)
            cands["Jornadas_Asignadas"] = cands["ID"].map(lambda x: len(staff_dates[x]))

            def jornada_ok(row):
                return len(staff_dates[row.ID]) < staff_max_jornadas[row.ID]
            
            def consecutive_ok(nurse_id):
                fechas_asignadas = staff_dates[nurse_id]
                if not fechas_asignadas: return True
                # Convertir todas las fechas a datetime.date y ordenarlas
                fechas_datetime = sorted([datetime.strptime(f, "%Y-%m-%d").date() for f in fechas_asignadas])
                fecha_actual = datetime.strptime(fecha, "%Y-%m-%d").date()
                # Verificar si la fecha_actual sería el 8vo día consecutivo
                consecutivos = 1
                for i in range(1, 8):
                    fecha_anterior = fecha_actual - timedelta(days=i)
                    if fecha_anterior in fechas_datetime:
                        consecutivos += 1
                    else: break
                return consecutivos < 8

            def descanso_12h_ok(nurse_id):
                fechas_previas = staff_dates[nurse_id]
                if not fechas_previas:
                    return True
                fecha_actual = datetime.strptime(fecha, "%Y-%m-%d")
                for fecha_ant in fechas_previas:
                    fecha_prev = datetime.strptime(fecha_ant, "%Y-%m-%d")
                    if abs((fecha_actual - fecha_prev).total_seconds()) < 12 * 3600:
                        return False
                return True

            def hours_ok(row):
                return staff_hours[row.ID] + SHIFT_HOURS[turno] <= staff_max_hours[row.ID]

            cands = cands[cands.apply(jornada_ok, axis=1)]
            cands = cands[cands["ID"].apply(consecutive_ok)]
            cands = cands[cands["ID"].apply(descanso_12h_ok)]
            cands = cands[cands.apply(hours_ok, axis=1)]
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
                    "Horas": SHIFT_HOURS[turno], 
                })
                staff_hours[cand.ID] += SHIFT_HOURS[turno]
                staff_dates[cand.ID].append(fecha)
                assigned_count += 1
        if assigned_count < req:
            uncovered.append({"Fecha": fecha, "Unidad": unidad, "Turno": turno, "Faltan": req - assigned_count})

    df_assign = pd.DataFrame(assignments)
 
    df_uncov = pd.DataFrame(uncovered) if uncovered else None 

    st.session_state.update({
        "asignacion_completada": True,
        "df_assign": df_assign,
        "df_uncov": pd.DataFrame(uncovered) if uncovered else None,
        "uncovered": uncovered 
    })

    df_assign["Fecha"] = pd.to_datetime(df_assign["Fecha"])
    df_assign["Año"] = df_assign["Fecha"].dt.year
    df_assign["Mes"] = df_assign["Fecha"].dt.month

    st.session_state["resumen_mensual"] = (df_assign.assign(
        Año=df_assign["Fecha"].dt.year,
        Mes=df_assign["Fecha"].dt.month
).groupby(["ID_Enfermera", "Unidad", "Turno", "Jornada", "Año", "Mes"])
 .agg(Horas_Asignadas=("Horas", "sum"),
      Jornadas_Asignadas=("Fecha", "count"))
 .reset_index()
 .rename(columns={"ID_Enfermera": "ID"}))

if st.session_state["asignacion_completada"]:
    df_assign = st.session_state["df_assign"].drop(columns=["Confirmado"], errors="ignore")
    uncovered = st.session_state.get("uncovered", [])
    st.success("✅ Asignación completada")
    st.markdown("""🔍Turnos asignados""")
    st.dataframe(df_assign)
    
    if uncovered:
        df_uncov = pd.DataFrame(uncovered)
        st.markdown("⚠️ Turnos sin cubrir")
        st.dataframe(df_uncov)
        # Solo mostrar botón si hay datos
        if not df_uncov.empty:
            unidad_descarga = unidad.replace(" ", "_")
            fecha_inicio_descarga = fecha_inicio
            fecha_fin_descarga = fecha_fin
            # Crear nombres de archivo
            file_name_uncov = f"Turnos_Descubiertos_{unidad_descarga}_{fecha_inicio_descarga.strftime('%Y%m%d')}_{fecha_fin_descarga.strftime('%Y%m%d')}.xlsx"
            st.download_button("⬇️ Descargar turnos sin cubrir", data=to_excel_bytes(df_uncov), file_name=file_name_uncov,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("### ✅ Confirmación de asignación")
    aprobacion = st.radio("¿Deseas aprobar esta asignación?", ["Pendiente", "Aprobar", "Rehacer"], index=0)
    
    if aprobacion == "Aprobar":
        # Debug: Mostrar estructura del DataFrame
        #st.write("Debug - df_assign columns:", st.session_state["df_assign"].columns)
        #st.write("Debug - df_assign dtypes:", st.session_state["df_assign"].dtypes)
        
        # Verificar columnas requeridas (asegurando que los nombres coincidan exactamente)
        required_cols = ["Fecha", "Unidad", "Turno", "ID_Enfermera", "Jornada", "Horas"]
        if not all(col in st.session_state["df_assign"].columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in st.session_state["df_assign"].columns]
            st.error(f"❌ Faltan columnas requeridas: {missing_cols}")
            st.stop()

        # Crear DataFrame para guardar (asegurando mayúsculas correctas)
        df_to_save = st.session_state["df_assign"][["Fecha", "Unidad", "Turno", "ID_Enfermera", "Jornada", "Horas"]].copy()
        df_to_save["Fecha"] = pd.to_datetime(df_to_save["Fecha"]).dt.strftime("%Y-%m-%d")

        # Guardar con validación - debug
        try:
            #st.write("Columnas en df_to_save:", df_to_save.columns.tolist())
            #st.write("Primeras filas:", df_to_save.head())
            guardar_asignaciones(df_to_save)
            guardar_resumen_mensual(st.session_state["resumen_mensual"])
            subir_bd_a_drive(FILE_ID)
            st.success("✅ Datos guardados en la base de datos correctamente.")
        except Exception as e:
            st.error(f"❌ Error al guardar: {str(e)}")

        if "resumen_mensual" not in st.session_state:
            st.error("No se encontró el resumen mensual")
            st.stop()

        # Obtener unidad y fechas de la demanda
        if metodo == "Desde Excel":
            if demand is not None and not demand.empty:
                # Extraer unidad (tomamos la primera que aparece)
                unidad_descarga = demand['Unidad'].iloc[0].replace(" ", "_")
                # Extraer rango de fechas
                fechas_demand = pd.to_datetime(demand['Fecha'])
                fecha_inicio_descarga = fechas_demand.min()
                fecha_fin_descarga = fechas_demand.max()
            else:
                st.error("⚠️No se ha cargado correctamente la demanda desde Excel")
                st.stop()
        else:
            # Usar los valores de cuando se generó desde la aplicación
            unidad_descarga = unidad.replace(" ", "_")
            fecha_inicio_descarga = fecha_inicio
            fecha_fin_descarga = fecha_fin

        # Crear nombres de archivo usando las variables correctas
        file_name_planilla = f"Turnos_Asignados_{unidad_descarga}_{fecha_inicio_descarga.strftime('%Y%m%d')}_{fecha_fin_descarga.strftime('%Y%m%d')}.xlsx"
        file_name_resumen = f"Resumen_{unidad_descarga}_{fecha_inicio_descarga.strftime('%Y%m%d')}_{fecha_fin_descarga.strftime('%Y%m%d')}.xlsx"
    
        st.download_button(
            "⬇️ Descargar planilla asignada", 
            data=to_excel_bytes(st.session_state["df_assign"].assign(Fecha=lambda x: pd.to_datetime(x['Fecha']).dt.strftime('%d/%m/%Y'))),
            file_name=file_name_planilla, 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.download_button(
            "⬇️ Descargar resumen por profesional", 
            data=to_excel_bytes(st.session_state["resumen_mensual"]), 
            file_name=file_name_resumen, 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    elif aprobacion == "Rehacer":
        st.session_state["asignacion_completada"] = False
        st.rerun()
        #st.experimental_rerun()

    if st.button("🔄 Reiniciar aplicación"):
        # Limpiar archivos subidos y datos de demanda
        keys_to_reset = [
            "file_staff", "df_assign", "df_uncov", "asignacion_completada",
            "uncovered", "resumen_mensual", "demand", "unidad", "fecha_inicio", "fecha_fin"
        ]
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        # Resetear valores por defecto del generador de demanda
        st.session_state.update({
            "unidad": "Medicina Interna",  # Valor por defecto
            "fecha_inicio": date(2025, 1, 1),
            "fecha_fin": date(2025, 1, 31),
        })
        st.rerun()  # Forzar recarga

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Resetear base de datos"):
    reset_db()
    st.session_state.clear()
    st.sidebar.success("✅ Base de datos reiniciada correctamente.")
    #st.experimental_rerun() #VERSION 04/08: comprobar si es necesario, ahora me da error
    #for key in list(st.session_state.keys()): #VERSION 31/07. Está al final del todo. El mensaje de reinicio correcto desaparece rápido...
        #del st.session_state[key]
    st.rerun()
