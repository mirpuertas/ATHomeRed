from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from datetime import date

from sqlalchemy import ForeignKey, text, Integer, Text, Date, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .perfiles import ProfesionalORM
    from .servicios import EspecialidadORM


class PublicacionORM(Base):
    __tablename__ = "publicacion"
    __table_args__ = (
        Index("ix_pub_profesional", "profesional_id"),
        Index("ix_pub_especialidad", "especialidad_id"),
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
    especialidad_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{SCHEMA}.especialidad.id_especialidad", ondelete="RESTRICT"),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_publicacion: Mapped[date] = mapped_column(Date, nullable=False)

    profesional: Mapped["ProfesionalORM"] = relationship(
        "ProfesionalORM", back_populates="publicaciones"
    )
    especialidad: Mapped["EspecialidadORM"] = relationship("EspecialidadORM")
