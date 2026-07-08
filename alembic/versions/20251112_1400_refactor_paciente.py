"""refactor_paciente_direccion_relacion

Revision ID: 20251112_1400_refactor_paciente
Revises: 20251112_1200_rm_prof_matricula
Create Date: 2025-11-12 14:00:00.000000

Refactor de tabla paciente:
1. Hacer relacion_id NOT NULL (siempre existe relación con solicitante)
2. Eliminar direccion_id (redundante con solicitante.direccion_id)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251112_1400_refactor_paciente"
down_revision = "20251112_1200_rm_prof_matricula"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Poblar relacion_id NULL con "Yo mismo" (id=35) si existen
    op.execute(
        """
        UPDATE athome.paciente 
        SET relacion_id = 35
        WHERE relacion_id IS NULL
    """
    )

    # 2. Hacer relacion_id NOT NULL
    with op.batch_alter_table("paciente", schema="athome") as batch_op:
        batch_op.alter_column("relacion_id", existing_type=sa.INTEGER(), nullable=False)

    # 3. Eliminar FK de direccion_id primero
    with op.batch_alter_table("paciente", schema="athome") as batch_op:
        batch_op.drop_constraint("paciente_direccion_id_fkey", type_="foreignkey")

    # 4. Eliminar columna direccion_id
    with op.batch_alter_table("paciente", schema="athome") as batch_op:
        batch_op.drop_column("direccion_id")


def downgrade() -> None:
    # 1. Recrear columna direccion_id
    with op.batch_alter_table("paciente", schema="athome") as batch_op:
        batch_op.add_column(
            sa.Column(
                "direccion_id", postgresql.UUID(), autoincrement=False, nullable=True
            )
        )

    # 2. Recrear FK a direccion
    with op.batch_alter_table("paciente", schema="athome") as batch_op:
        batch_op.create_foreign_key(
            "paciente_direccion_id_fkey",
            "direccion",
            ["direccion_id"],
            ["id"],
            source_schema="athome",
            referent_schema="athome",
            ondelete="SET NULL",
        )

    # 3. Hacer relacion_id nullable de nuevo
    with op.batch_alter_table("paciente", schema="athome") as batch_op:
        batch_op.alter_column("relacion_id", existing_type=sa.INTEGER(), nullable=True)
