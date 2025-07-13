import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("turnos_sermas.db")

# ──────────────────────── CREACIÓN Y CONEXIÓN ─────────────────────────
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Tabla para acumular horas
        c.execute("""
        CREATE TABLE IF NOT EXISTS horas_acumuladas (
            ID TEXT PRIMARY KEY,
            Turno_Contrato TEXT,
            Horas_Acumuladas REAL
        )
        """)
        # Tabla para guardar asignaciones mensuales
        c.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones (
            Fecha TEXT,
            Unidad TEXT,
            Turno TEXT,
            ID_Enfermera TEXT,
            Jornada TEXT,
            Horas_Acumuladas REAL
        )
        """)
        conn.commit()

# ──────────────────────── FUNCIONES DE GUARDADO ───────────────────────
def guardar_horas(df_resumen):
    with sqlite3.connect(DB_PATH) as conn:
        df_resumen.to_sql("horas_acumuladas", conn, if_exists="replace", index=False)

def guardar_asignaciones(df_planilla):
    with sqlite3.connect(DB_PATH) as conn:
        df_planilla.to_sql("asignaciones", conn, if_exists="append", index=False)

# ──────────────────────── LECTURA DE HORAS PREVIAS ────────────────────
def cargar_horas():
    with sqlite3.connect(DB_PATH) as conn:
        try:
            df = pd.read_sql("SELECT * FROM horas_acumuladas", conn)
            return df
        except Exception:
            return pd.DataFrame(columns=["ID", "Turno_Contrato", "Horas_Acumuladas"])
