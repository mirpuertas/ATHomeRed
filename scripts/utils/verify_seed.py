"""
Script para verificar los datos cargados por el seed
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()


def verify_seed():
    """Verifica los datos cargados"""
    db_url = os.getenv("SUPABASE_DB_URL")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    print("=" * 70)
    print("VERIFICACIÓN DE DATOS CARGADOS - AtHomeRed")
    print("=" * 70)
    print()

    queries = [
        ("Provincias", "SELECT COUNT(*) FROM athome.provincia"),
        ("Departamentos", "SELECT COUNT(*) FROM athome.departamento"),
        ("Barrios", "SELECT COUNT(*) FROM athome.barrio"),
        ("Direcciones", "SELECT COUNT(*) FROM athome.direccion"),
        ("Especialidades", "SELECT COUNT(*) FROM athome.especialidad"),
        ("Relaciones", "SELECT COUNT(*) FROM athome.relacion_solicitante"),
        ("Usuarios", "SELECT COUNT(*) FROM athome.usuario"),
        ("Profesionales", "SELECT COUNT(*) FROM athome.profesional"),
        (
            "Profesional-Especialidad",
            "SELECT COUNT(*) FROM athome.profesional_especialidad",
        ),
        ("Matrículas", "SELECT COUNT(*) FROM athome.matricula"),
        ("Solicitantes", "SELECT COUNT(*) FROM athome.solicitante"),
        ("Pacientes", "SELECT COUNT(*) FROM athome.paciente"),
        ("Publicaciones", "SELECT COUNT(*) FROM athome.publicacion"),
        ("Disponibilidades", "SELECT COUNT(*) FROM athome.disponibilidad"),
    ]

    print("CONTEO DE REGISTROS:")
    print("-" * 70)
    for label, query in queries:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"  {label:<30} {count:>5}")

    print()
    print("-" * 70)
    print()

    print("DISTRIBUCIÓN DE PROFESIONALES POR ESPECIALIDAD:")
    print("-" * 70)
    cursor.execute(
        """
        SELECT e.nombre, COUNT(pe.profesional_id) AS cantidad
        FROM athome.especialidad e
        LEFT JOIN athome.profesional_especialidad pe ON e.id_especialidad = pe.especialidad_id
        GROUP BY e.nombre ORDER BY cantidad DESC
    """
    )
    for row in cursor.fetchall():
        print(f"  {row[0]:<50} {row[1]:>5}")

    print()
    print("-" * 70)
    print()

    print("DISTRIBUCIÓN DE PACIENTES POR RELACIÓN:")
    print("-" * 70)
    cursor.execute(
        """
        SELECT r.nombre, COUNT(p.id) AS cantidad
        FROM athome.relacion_solicitante r
        LEFT JOIN athome.paciente p ON r.id = p.relacion_id
        GROUP BY r.nombre ORDER BY cantidad DESC
    """
    )
    for row in cursor.fetchall():
        if row[1] > 0:
            print(f"  {row[0]:<30} {row[1]:>5}")

    print()
    print("=" * 70)
    print("VERIFICACIÓN COMPLETADA")
    print("=" * 70)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    verify_seed()
