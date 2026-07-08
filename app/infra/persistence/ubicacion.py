from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import (
    UniqueConstraint,
    Index,
    CheckConstraint,
    Float,
    ForeignKey,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, VARCHAR as Varchar
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA


class ProvinciaORM(Base):
    __tablename__ = "provincia"
    __table_args__ = (
        UniqueConstraint("nombre", name="uq_provincia_nombre"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    nombre: Mapped[str] = mapped_column(Varchar(50), nullable=False)

    departamentos: Mapped[List["DepartamentoORM"]] = relationship(
        back_populates="provincia", cascade="all, delete-orphan"
    )


class DepartamentoORM(Base):
    __tablename__ = "departamento"
    __table_args__ = (
        UniqueConstraint(
            "provincia_id", "nombre", name="uq_departamento_provincia_nombre"
        ),
        Index("ix_departamento_provincia", "provincia_id"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    provincia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.provincia.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(Varchar(50), nullable=False)

    provincia: Mapped["ProvinciaORM"] = relationship(back_populates="departamentos")
    barrios: Mapped[List["BarrioORM"]] = relationship(
        back_populates="departamento", cascade="all, delete-orphan"
    )


class BarrioORM(Base):
    __tablename__ = "barrio"
    __table_args__ = (
        UniqueConstraint(
            "departamento_id", "nombre", name="uq_barrio_departamento_nombre"
        ),
        Index("ix_barrio_departamento", "departamento_id"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    departamento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.departamento.id", ondelete="RESTRICT"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(Varchar(50), nullable=False)

    departamento: Mapped["DepartamentoORM"] = relationship(back_populates="barrios")
    direcciones: Mapped[List["DireccionORM"]] = relationship(
        back_populates="barrio", cascade="all, delete-orphan"
    )


class DireccionORM(Base):
    __tablename__ = "direccion"
    __table_args__ = (
        Index("ix_direccion_barrio", "barrio_id"),
        CheckConstraint(
            "(latitud is null and longitud is null) or (latitud between -90 and 90 and longitud between -180 and 180)",
            name="ck_dir_latlon",
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    barrio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.barrio.id", ondelete="RESTRICT"),
        nullable=False,
    )
    calle: Mapped[str] = mapped_column(Varchar(100), nullable=False)
    numero: Mapped[int] = mapped_column(nullable=False)
    latitud: Mapped[Optional[float]] = mapped_column(Float)
    longitud: Mapped[Optional[float]] = mapped_column(Float)

    barrio: Mapped["BarrioORM"] = relationship(back_populates="direcciones")
