# 🩺 Planificador de Turnos de Enfermería – SERMAS

Proyecto desarrollado como parte del **Trabajo Fin de Máster (TFM) en Gestión Sanitaria**. Automatiza la planificación de turnos de enfermería en hospitales públicos del Servicio Madrileño de Salud (SERMAS) cumpliendo criterios normativos y reduciendo la carga administrativa de las supervisoras.

---

## 🌟 Funcionalidades principales

| Paso | Acción | Descripción |
|------|--------|-------------|
| 1️⃣  | Configurar demanda semanal | En la interfaz web se define cuántas enfermeras se necesitan por turno (mañana, tarde, noche) para cada día de la semana. Esta configuración se aplica a los **365 días del año**. |
| 2️⃣  | Subir plantilla de personal | Archivo Excel con columnas:<br/>`ID`, `Unidad_Asignada`, `Jornada`, `Turno_Contrato`, `Fechas_No_Disponibilidad`. |
| 3️⃣  | Ejecutar asignación | El motor asigna turnos cumpliendo:<br/>• Máx. **8 días consecutivos**<br/>• Límite anual **1667,5 h** (diurnas) / **1490 h** (nocturnas)<br/>• Compatibilidad de unidad y turno<br/>• Fechas de no disponibilidad |
| 4️⃣  | Descargar resultados | Descarga dos Excel:<br/>• `Planilla_Asignada.xlsx`<br/>• `Turnos_Sin_Cubrir.xlsx` (si aplica) |

---

## 🚀 Despliegue rápido en Streamlit Cloud

1. **Fork o clona** este repositorio en tu cuenta de GitHub.
2. Ve a **[streamlit.io/cloud](https://streamlit.io/cloud)** y conecta tu cuenta de GitHub.
3. Crea una nueva app seleccionando el repositorio y el archivo **`app.py`**.
4. ¡Listo! Tendrás un enlace público para compartir con las supervisoras.

---

## 📂 Estructura del proyecto

```
tfm-turnos/
├── app.py              # Interfaz única (demanda + asignación)
├── requirements.txt    # Dependencias
├── README.md           # Este documento
└── .gitignore          # Exclusiones de Git
```

> **Nota:** Los archivos `asignador.py` y `generador_demanda.py` se han fusionado en `app.py` para simplificar el flujo.

---

## ⚙️ Dependencias

```
streamlit>=1.32.0
pandas>=2.0.0
openpyxl>=3.1.2
```

Instala localmente con:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🛡️ Licencia y uso

Todo el código y material están protegidos por **derechos de autor** (© 2025 Laura López Acedo). Queda prohibida su copia, modificación o distribución sin autorización expresa de la autora.

---

## ✉️ Contacto

Para dudas o colaboración, abre un *issue* en GitHub o escribe a **laura.lopez@example.com**.
