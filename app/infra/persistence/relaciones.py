from __future__ import annotations
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, SCHEMA


class RelacionSolicitanteORM(Base):
    __tablename__ = "relacion_solicitante"
    __table_args__ = (
        UniqueConstraint("nombre", name="uq_rel_solicitante_nombre"),
        {"schema": SCHEMA},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(unique=True, nullable=False)
