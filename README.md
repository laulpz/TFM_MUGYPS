
# 🩺 Planificador de Turnos de Enfermería

Aplicación web interactiva para asignar turnos de enfermería en hospitales públicos del Servicio Madrileño de Salud (SERMAS). Permite automatizar la planificación teniendo en cuenta criterios reales como jornadas, turnos contratados, fechas de no disponibilidad y límites legales de horas.

## 🚀 Funcionalidades
- **Asignador de Turnos**: Asignación automática basada en disponibilidad, jornadas y límites legales.
      - Turnos respetando contrato, unidad, jornada y ausencias.
      - Límite de **8 jornadas consecutivas**.
      - Control del máximo de horas anuales (1667,5 h diurno, 1490 h nocturno).
- Selección de **rango de fechas** personalizado (planificación mensual, trimestral, etc.).
- **Generador de Demanda**: Configuración interactiva de necesidades por unidad y fecha.
- **Informes**: Visualización y descarga de resúmenes mensuales.

- **Persistencia de datos** en base de datos SQLite local:
  - Registro de asignaciones anteriores.
  - Acumulación de horas por enfermera.
- Descarga de:
  - 📋 Planilla asignada.
  - ⚠️ Turnos sin cubrir.
  - 📊 Resumen de horas.

## 🧾 Estructura esperada del archivo de plantilla de personal

| ID     | Unidad_Asignada | Jornada   | Turno_Contrato | Fechas_No_Disponibilidad     |
|--------|------------------|-----------|----------------|------------------------------|
| E001   | Medicina Interna | Completa  | Mañana         | 2025-01-05, 2025-01-06       |
| E002   | UCI              | Parcial   | Noche          |                              |

- `Fechas_No_Disponibilidad`: fechas separadas por coma (puede dejarse vacío).
- `Turno_Contrato`: solo uno permitido por persona.

## 🛠️ Estructura del Proyecto
```plaintext
/pages           # Módulos de la app (Streamlit)
  - 1_Asignador.py
  - 2_Generador_Demanda.py
  - 3_Informe.py
/utils           # Funciones compartidas (ej: excel_utils.py)
app.py           # Interfaz principal
db_manager.py    # Gestión de base de datos
```

## 🖥️ Cómo ejecutar

```bash
streamlit run app.py
```

> ⚠️ Requiere `db_manager.py` en el mismo directorio.

## 📂 Archivos clave

- `app.py` → interfaz y lógica principal.
- `db_manager.py` → conexión y gestión de SQLite.
- `planilla.xlsx` → plantilla de personal de entrada.
- `asignaciones.db` → base de datos local con horas y asignaciones.

## 📌 Ejemplo de uso

1. Sube el archivo de personal
2. Selecciona el rango de fechas a planificar.
3. Introduce la demanda para cada turno.
5. Ejecuta la asignación y aprueba o rechaza la propuesta
6. Descarga los archivos generados.
7. Ve a la pestaña Informe para visualizar la asignación en formato más visual

## 📃 Licencia

Este proyecto está protegido por derechos de autor. Su uso y distribución están restringidos salvo autorización de la autora.
