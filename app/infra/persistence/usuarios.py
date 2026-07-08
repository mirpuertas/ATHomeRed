from __future__ import annotations
import uuid
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import (
    UniqueConstraint,
    CheckConstraint,
    text,
    DateTime,
    String,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID, VARCHAR as Varchar
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, SCHEMA

if TYPE_CHECKING:
    pass


class UsuarioORM(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        UniqueConstraint("email", name="uq_usuario_email"),
        CheckConstraint(
            "NOT (es_profesional = TRUE AND es_solicitante = TRUE)",
            name="ck_usuario_roles_exclusivos",
        ),
        CheckConstraint(
            "(es_profesional = TRUE) OR (es_solicitante = TRUE)",
            name="ck_usuario_al_menos_un_rol",
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    nombre: Mapped[str] = mapped_column(Varchar(50), nullable=False)
    apellido: Mapped[str] = mapped_column(Varchar(50), nullable=False)
    email: Mapped[str] = mapped_column(Varchar(50), nullable=False)
    celular: Mapped[Optional[str]] = mapped_column(Varchar(50))

    es_solicitante: Mapped[bool] = mapped_column(default=True, nullable=False)
    es_profesional: Mapped[bool] = mapped_column(default=False, nullable=False)

    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ultimo_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bloqueado_hasta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)
    verificado: Mapped[bool] = mapped_column(default=False, nullable=False)

    refresh_tokens = relationship(
        "RefreshTokenORM",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
