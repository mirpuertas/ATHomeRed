"""
Script para verificar/crear el esquema 'athome' en la base de datos.
Ejecutar ANTES de la primera migración de Alembic.
"""

import sys
from pathlib import Path
from sqlalchemy import text

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.infra.persistence.database import ENGINE  # noqa: E402
from app.infra.persistence.base import SCHEMA  # noqa: E402


def crear_esquema():
    """Crea el esquema athome si no existe."""
    print(f"Verificando esquema '{SCHEMA}'...")

    with ENGINE.connect() as connection:
        result = connection.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"
            ),
            {"schema": SCHEMA},
        )

        existe = result.fetchone() is not None

        if existe:
            print(f"El esquema '{SCHEMA}' ya existe.")
            return True

        print(f"Creando esquema '{SCHEMA}'...")
        connection.execute(text(f"CREATE SCHEMA {SCHEMA}"))
        connection.commit()
        print(f"Esquema '{SCHEMA}' creado exitosamente.")
        return True


def main():
    try:
        crear_esquema()
        print("\n ¡Listo! Ahora puedes ejecutar:")
        print("   alembic revision --autogenerate -m 'initial migration'")
        print("   alembic upgrade head")
        return 0
    except Exception as e:
        print(f"\n Error: {e}")
        print("\n Asegúrate de:")
        print("   1. Tener las credenciales correctas en .env")
        print("   2. Tener conexión a la base de datos")
        print("   3. Tener permisos para crear esquemas")
        return 1


if __name__ == "__main__":
    sys.exit(main())
