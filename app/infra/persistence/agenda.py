from __future__ import annotations

import uuid
from datetime import date, time
from typing import List, Dict, Any, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Index,
    ForeignKey,
    JSON,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .perfiles import ProfesionalORM
    from .paciente import PacienteORM
    from .ubicacion import DireccionORM


class DisponibilidadORM(Base):
    __tablename__ = "disponibilidad"
    __table_args__ = (
        CheckConstraint("hora_inicio < hora_fin", name="ck_disp_horas"),
        Index("ix_disp_profesional", "profesional_id"),
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
    dias_semana_text: Mapped[str] = mapped_column("dias_semana", Text, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(nullable=False)
    hora_fin: Mapped[time] = mapped_column(nullable=False)

    profesional: Mapped["ProfesionalORM"] = relationship(
        "ProfesionalORM", back_populates="disponibilidades"
    )

    @property
    def dias_semana(self) -> list[str]:
        return [s for s in (self.dias_semana_text or "").split(",") if s]

    @dias_semana.setter
    def dias_semana(self, value: list[str]) -> None:
        self.dias_semana_text = ",".join(value or [])


class EstadoConsultaORM(Base):
    __tablename__ = "estado_consulta"
    __table_args__ = (
        UniqueConstraint("codigo", name="uq_estado_consulta_codigo"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(nullable=False)
    descripcion: Mapped[str] = mapped_column(nullable=False)


class ConsultaORM(Base):
    __tablename__ = "consulta"
    __table_args__ = (
        CheckConstraint("hora_inicio < hora_fin", name="ck_consulta_horas"),
        Index("ix_consulta_profesional", "profesional_id"),
        Index("ix_consulta_paciente", "paciente_id"),
        Index("ix_consulta_fecha", "fecha"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.paciente.id", ondelete="CASCADE"),
        nullable=False,
    )

    profesional_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.profesional.id", ondelete="CASCADE"),
        nullable=False,
    )
    direccion_servicio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.direccion.id", ondelete="RESTRICT"),
        nullable=False,
    )

    fecha: Mapped[date] = mapped_column(nullable=False)
    hora_inicio: Mapped[time] = mapped_column(nullable=False)
    hora_fin: Mapped[time] = mapped_column(nullable=False)

    estado_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA}.estado_consulta.id", ondelete="RESTRICT"),
        nullable=False,
    )

    notas: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))

    paciente: Mapped["PacienteORM"] = relationship(
        "PacienteORM", back_populates="consultas"
    )
    profesional: Mapped["ProfesionalORM"] = relationship(
        "ProfesionalORM", back_populates="consultas"
    )
    direccion_servicio: Mapped["DireccionORM"] = relationship("DireccionORM")
    estado: Mapped["EstadoConsultaORM"] = relationship("EstadoConsultaORM")

    eventos: Mapped[List["EventoORM"]] = relationship(
        "EventoORM",
        back_populates="consulta",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EventoORM(Base):
    __tablename__ = "evento"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    consulta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.consulta.id", ondelete="CASCADE"),
        nullable=False,
    )

    tipo: Mapped[str] = mapped_column(nullable=False)

    datos: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    consulta: Mapped["ConsultaORM"] = relationship(
        "ConsultaORM",
        back_populates="eventos",
    )
