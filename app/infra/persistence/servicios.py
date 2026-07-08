from __future__ import annotations

from decimal import Decimal

from typing import List, TYPE_CHECKING

from sqlalchemy import Table, Column, Integer, Numeric, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, VARCHAR as Varchar
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .perfiles import ProfesionalORM


class EspecialidadORM(Base):
    __tablename__ = "especialidad"
    __table_args__ = ({"schema": SCHEMA},)

    id_especialidad: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    nombre: Mapped[str] = mapped_column(Varchar(80), nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    tarifa: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    profesionales: Mapped[List["ProfesionalORM"]] = relationship(
        "ProfesionalORM",
        secondary=lambda: profesional_especialidad,
        back_populates="especialidades",
    )


profesional_especialidad = Table(
    "profesional_especialidad",
    Base.metadata,
    Column(
        "profesional_id",
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.profesional.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "especialidad_id",
        Integer,
        ForeignKey(f"{SCHEMA}.especialidad.id_especialidad", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema=SCHEMA,
)

Index(
    "ix_prof_esp_profesional",
    profesional_especialidad.c.profesional_id,
)
Index(
    "ix_prof_esp_especialidad",
    profesional_especialidad.c.especialidad_id,
)
