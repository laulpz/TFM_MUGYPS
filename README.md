# 🩺 Asignador Automático de Turnos para Enfermería (SERMAS)

Este proyecto forma parte del Trabajo Fin de Máster (TFM) del Máster en Gestión Sanitaria. Su objetivo es automatizar la planificación de turnos de enfermería en hospitales públicos del Servicio Madrileño de Salud (SERMAS), respetando las limitaciones normativas y mejorando la eficiencia administrativa.

---

## 📌 Funcionalidades

### 1. **Generador interactivo de demanda de turnos**

* Permite a las supervisoras definir cuántos profesionales necesitan por turno (mañana, tarde, noche) para cada día de la semana.
* A partir de esta entrada, se genera automáticamente un archivo `.xlsx` con la demanda para los 365 días del año.
* Pensado para simplificar la introducción de datos sin editar manualmente archivos largos.

### 2. **Asignador automático de turnos**

* Asigna turnos a las enfermeras teniendo en cuenta:

  * Jornada (completa o parcial)
  * Turno contratado (mañana, tarde o noche)
  * Fechas de no disponibilidad
  * Límite anual de horas: 1667,5 h diurnas o 1490 h nocturnas
  * Máximo de 8 jornadas consecutivas trabajadas
  * Equilibrio en la carga de trabajo

* Genera dos archivos Excel:

  * 📋 `Planilla_Asignada.xlsx`: turnos asignados
  * ⚠️ `Turnos_Sin_Cubrir.xlsx`: turnos que no se pudieron cubrir

---

## 📂 Estructura del proyecto

```
tfm-turnos/
├── app.py                      # Script principal con pestañas de navegación
├── generador_demanda.py       # Formulario interactivo para crear demanda
├── asignador.py               # Motor de asignación de turnos
├── requirements.txt           # Dependencias del proyecto
└── README.md                  # Este archivo explicativo
```

---

## 🚀 Cómo desplegar en Streamlit Cloud

1. **Sube el proyecto a GitHub** (con esta estructura).
2. Entra en [https://streamlit.io/cloud](https://streamlit.io/cloud) y conecta tu cuenta de GitHub.
3. Selecciona el repositorio y el archivo `app.py` como script de entrada.
4. ¡Listo! La app estará en línea para pruebas o uso real.

---

## ⚙️ Requisitos

```
streamlit>=1.32.0
pandas>=2.0.0
openpyxl>=3.1.2
```

---

## 📬 Contacto

Proyecto desarrollado por **Laura López Acedo** como parte del Máster en Gestión Sanitaria.

Para más información o colaboración, contacta a través de [GitHub](https://github.com/).

---

## 🛡️ Licencia

Este software no se distribuye libremente ni se autoriza su reproducción sin el consentimiento expreso de la autora. Todos los derechos reservados.


