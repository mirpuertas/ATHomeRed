"""remove_prof_matricula

Revision ID: 20251112_1200_rm_prof_matricula
Revises: 61513ea4632b
Create Date: 2025-11-12 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251112_1200_rm_prof_matricula"
down_revision = "61513ea4632b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop redundant column 'matricula' from athome.profesional
    with op.batch_alter_table("profesional", schema="athome") as batch_op:
        batch_op.drop_column("matricula")


def downgrade() -> None:
    # Recreate column on downgrade
    with op.batch_alter_table("profesional", schema="athome") as batch_op:
        batch_op.add_column(
            sa.Column("matricula", sa.VARCHAR(length=50), nullable=True)
        )
