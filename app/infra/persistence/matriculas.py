from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    UniqueConstraint,
    CheckConstraint,
    Index,
    ForeignKey,
    text,
    Date,
)
from sqlalchemy.dialects.postgresql import UUID, VARCHAR as Varchar
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .perfiles import ProfesionalORM
    from .ubicacion import ProvinciaORM


class MatriculaORM(Base):
    __tablename__ = "matricula"
    __table_args__ = (
        UniqueConstraint(
            "profesional_id",
            "provincia_id",
            "nro_matricula",
            name="uq_matricula_prof_prov_nro",
        ),
        CheckConstraint("vigente_hasta >= vigente_desde", name="ck_matricula_fechas"),
        Index("ix_matricula_profesional", "profesional_id"),
        Index("ix_matricula_provincia", "provincia_id"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    profesional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.profesional.id", ondelete="CASCADE"),
        nullable=False,
    )
    provincia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.provincia.id", ondelete="RESTRICT"),
        nullable=False,
    )

    nro_matricula: Mapped[str] = mapped_column(Varchar(50), nullable=False)

    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[date] = mapped_column(Date, nullable=False)

    profesional: Mapped["ProfesionalORM"] = relationship(
        "ProfesionalORM", back_populates="matriculas"
    )
    provincia: Mapped["ProvinciaORM"] = relationship("ProvinciaORM")
