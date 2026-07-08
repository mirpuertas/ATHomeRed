from __future__ import annotations

import uuid
from datetime import date

from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Text,
    text,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .perfiles import SolicitanteORM
    from .relaciones import RelacionSolicitanteORM
    from .agenda import ConsultaORM
    from .valoraciones import ValoracionORM


class PacienteORM(Base):
    __tablename__ = "paciente"
    __table_args__ = (
        UniqueConstraint(
            "solicitante_id", name="uq_paciente_solicitante"
        ),  # fuerza 1–1
        CheckConstraint(
            "fecha_nacimiento IS NULL OR fecha_nacimiento <= CURRENT_DATE",
            name="ck_paciente_fecha_nac_pasada",
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    apellido: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(nullable=True)
    notas: Mapped[str] = mapped_column(Text, default="", nullable=False)

    solicitante_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.solicitante.id", ondelete="CASCADE"),
        nullable=False,
    )

    relacion_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA}.relacion_solicitante.id", ondelete="RESTRICT"),
        nullable=False,
    )

    solicitante: Mapped["SolicitanteORM"] = relationship(
        "SolicitanteORM", back_populates="paciente", uselist=False
    )

    relacion: Mapped["RelacionSolicitanteORM"] = relationship("RelacionSolicitanteORM")

    consultas: Mapped[List["ConsultaORM"]] = relationship(
        "ConsultaORM",
        back_populates="paciente",
        cascade="all, delete-orphan",
    )

    valoraciones: Mapped[List["ValoracionORM"]] = relationship(
        "ValoracionORM",
        back_populates="paciente",
        cascade="all, delete-orphan",
    )
