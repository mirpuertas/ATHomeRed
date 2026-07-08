from __future__ import annotations

import uuid
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import UniqueConstraint, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA
from .servicios import (
    profesional_especialidad,
)

if TYPE_CHECKING:
    from .usuarios import UsuarioORM
    from .ubicacion import DireccionORM
    from .servicios import EspecialidadORM
    from .agenda import DisponibilidadORM, ConsultaORM
    from .publicaciones import PublicacionORM
    from .matriculas import MatriculaORM
    from .valoraciones import ValoracionORM
    from .paciente import PacienteORM


class ProfesionalORM(Base):
    __tablename__ = "profesional"
    __table_args__ = (
        UniqueConstraint("usuario_id", name="uq_profesional_usuario"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.usuario.id", ondelete="CASCADE"),
        nullable=False,
    )

    direccion_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.direccion.id", ondelete="SET NULL"),
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    verificado: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )

    usuario: Mapped["UsuarioORM"] = relationship("UsuarioORM")
    direccion: Mapped[Optional["DireccionORM"]] = relationship("DireccionORM")

    especialidades: Mapped[List["EspecialidadORM"]] = relationship(
        "EspecialidadORM",
        secondary=profesional_especialidad,
        lazy="joined",
        back_populates="profesionales",
    )

    disponibilidades: Mapped[List["DisponibilidadORM"]] = relationship(
        "DisponibilidadORM",
        back_populates="profesional",
        cascade="all, delete-orphan",
    )

    publicaciones: Mapped[List["PublicacionORM"]] = relationship(
        "PublicacionORM",
        back_populates="profesional",
        cascade="all, delete-orphan",
    )

    matriculas: Mapped[List["MatriculaORM"]] = relationship(
        "MatriculaORM",
        back_populates="profesional",
        cascade="all, delete-orphan",
    )

    valoraciones: Mapped[List["ValoracionORM"]] = relationship(
        "ValoracionORM",
        back_populates="profesional",
        cascade="all, delete-orphan",
    )

    consultas: Mapped[List["ConsultaORM"]] = relationship(
        "ConsultaORM",
        back_populates="profesional",
        cascade="all, delete-orphan",
    )


class SolicitanteORM(Base):
    __tablename__ = "solicitante"
    __table_args__ = (
        UniqueConstraint("usuario_id", name="uq_solicitante_usuario"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.usuario.id", ondelete="CASCADE"),
        nullable=False,
    )

    direccion_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.direccion.id", ondelete="SET NULL"),
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))

    usuario: Mapped["UsuarioORM"] = relationship("UsuarioORM")
    direccion: Mapped[Optional["DireccionORM"]] = relationship("DireccionORM")

    paciente: Mapped[Optional["PacienteORM"]] = relationship(
        "PacienteORM",
        back_populates="solicitante",
        cascade="all, delete-orphan",
        uselist=False,
    )
