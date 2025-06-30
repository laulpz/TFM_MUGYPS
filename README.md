# Asignador de Turnos de Enfermería

Esta aplicación web permite automatizar la planificación de turnos de enfermería en hospitales públicos, facilitando el trabajo de las supervisoras de enfermería. Desarrollada como parte de un Trabajo Fin de Máster (TFM) en Gestión Sanitaria.

## Características

- Subida de datos del personal y demanda de turnos en formato Excel.
- Asignación automática teniendo en cuenta disponibilidad, unidad, experiencia y turno preferido.
- Visualización y descarga de la planilla generada.
- Interfaz accesible a través de Streamlit Cloud.

## Uso

1. Sube los archivos `Enfermeras_Simuladas_TFM.xlsx` y `Demanda_Turnos_TFM.xlsx`.
2. Marca las opciones deseadas en la barra lateral.
3. Ejecuta la asignación y descarga el resultado.

## Requisitos

- Python 3.8+
- Streamlit
- Pandas
- openpyxl

## Despliegue en Streamlit Cloud

1. Sube este repositorio a tu cuenta de GitHub.
2. Ve a [streamlit.io/cloud](https://streamlit.io/cloud) e inicia sesión.
3. Crea una nueva app desde tu repositorio seleccionando:
   - Branch: `main`
   - Main file: `asignador_turnos.py`
4. ¡Listo! Tu app estará disponible públicamente.

## Autor

Laura López Acedo — TFM Máster en Gestión Sanitaria

