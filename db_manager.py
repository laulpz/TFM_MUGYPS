
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("turnos.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS asignaciones (
            Fecha TEXT,
            Unidad TEXT,
            Turno TEXT,
            ID_Enfermera TEXT,
            Jornada TEXT,
            Horas_Acumuladas REAL,
            Confirmado INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def guardar_asignaciones(df):
    conn = sqlite3.connect(DB_PATH)
    df["Confirmado"] = df.get("Confirmado", 0)
    df.to_sql("asignaciones", conn, if_exists="append", index=False)
    conn.close()

def cargar_asignaciones(confirmado=True):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM asignaciones"
    if confirmado:
        query += " WHERE Confirmado = 1"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def confirmar_asignaciones():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE asignaciones SET Confirmado = 1 WHERE Confirmado = 0")
    conn.commit()
    conn.close()

def reset_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS asignaciones")
    conn.commit()
    conn.close()
    init_db()  # recrea la tabla después de borrarla
