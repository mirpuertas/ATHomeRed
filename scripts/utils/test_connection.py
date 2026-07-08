"""
Script para probar la conexión a la base de datos
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def test_connection():
    """Prueba la conexión a la base de datos"""
    print("=" * 60)
    print("PROBANDO CONEXIÓN A BASE DE DATOS")
    print("=" * 60)

    try:
        from app.infra.persistence.database import ENGINE, DATABASE_URL

        masked_url = str(DATABASE_URL)
        if "://" in masked_url and "@" in masked_url:
            prefix, rest = masked_url.split("://", 1)
            if "@" in rest:
                creds, tail = rest.split("@", 1)
                if ":" in creds:
                    user, pwd = creds.split(":", 1)
                    creds = f"{user}:***"
                masked_url = f"{prefix}://{creds}@{tail}"

        print(f"\n URL: {masked_url}")

        print("\n Intentando conectar...")
        from sqlalchemy import text

        with ENGINE.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Conexión exitosa!")

            if "postgresql" in str(DATABASE_URL):
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"\n PostgreSQL: {version[:50]}...")
            elif "sqlite" in str(DATABASE_URL):
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                print(f"\n SQLite versión: {version}")

        print("\n" + "=" * 60)
        print(" Todo OK - Base de datos accesible")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n ERROR: {e}")
        print("\n Verifica:")
        print("   1. El archivo .env existe y tiene las credenciales correctas")
        print("   2. La base de datos está corriendo (PostgreSQL/MySQL)")
        print("   3. Las credenciales son válidas")
        print("   4. El host y puerto son correctos")
        print("\n" + "=" * 60)
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
