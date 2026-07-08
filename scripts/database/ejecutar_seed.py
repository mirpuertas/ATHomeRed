"""
Script para ejecutar el seed SQL completo en la base de datos.
"""

from pathlib import Path
from sqlalchemy import text
from app.infra.persistence.database import SessionLocal


def ejecutar_seed():
    seed_file = Path(__file__).parent / "seed_completo_uuid.sql"

    if not seed_file.exists():
        print(f"ERROR: No se encuentra el archivo {seed_file}")
        return

    print("=" * 80)
    print("EJECUTANDO SEED COMPLETO")
    print("=" * 80)

    with open(seed_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    session = SessionLocal()

    try:
        print(f"\nEjecutando SQL desde {seed_file.name}...")
        session.execute(text(sql_content))
        session.commit()
        print("\n✓ Seed ejecutado exitosamente")

        # Mostrar resumen
        print("\n" + "=" * 80)
        print("RESUMEN DE DATOS CARGADOS")
        print("=" * 80)

        tablas = [
            "provincia",
            "departamento",
            "barrio",
            "direccion",
            "especialidad",
            "estado_consulta",
            "relacion_solicitante",
            "profesional",
            "solicitante",
            "paciente",
            "publicacion",
            "disponibilidad",
            "matricula",
        ]

        for tabla in tablas:
            count = session.execute(
                text(f"SELECT COUNT(*) FROM athome.{tabla}")
            ).scalar()
            print(f"  {tabla}: {count} registros")

        print("=" * 80)

    except Exception as e:
        session.rollback()
        print(f"\n✗ ERROR al ejecutar seed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    ejecutar_seed()
