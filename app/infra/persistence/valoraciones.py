from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING
from datetime import date

from sqlalchemy import (
    Index,
    CheckConstraint,
    ForeignKey,
    text,
    Date,
    Integer,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .perfiles import ProfesionalORM
    from .paciente import PacienteORM


class ValoracionORM(Base):
    __tablename__ = "valoracion"
    __table_args__ = (
        CheckConstraint(
            "puntuacion BETWEEN 1 AND 5", name="ck_valoracion_puntuacion_1_5"
        ),
        Index("ix_valoracion_profesional_fecha", "profesional_id", "creado_en"),
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
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.paciente.id", ondelete="CASCADE"),
        nullable=False,
    )
    puntuacion: Mapped[int] = mapped_column(Integer, nullable=False)
    comentario: Mapped[Optional[str]] = mapped_column(Text)
    creado_en: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=text("CURRENT_DATE")
    )

    profesional: Mapped["ProfesionalORM"] = relationship(
        "ProfesionalORM", back_populates="valoraciones"
    )
    paciente: Mapped["PacienteORM"] = relationship(
        "PacienteORM", back_populates="valoraciones"
    )
