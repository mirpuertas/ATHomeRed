"""
Modelos ORM para autenticación y auditoría.
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    text,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base, SCHEMA


class RefreshTokenORM(Base):
    """Tabla para almacenar refresh tokens JWT."""

    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": SCHEMA}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True,
    )
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey(f"{SCHEMA}.usuario.id"),
        nullable=False,
        index=True,
    )
    token = Column(String(500), unique=True, nullable=False, index=True)
    expira_en = Column(DateTime, nullable=False)
    revocado = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    creado_en = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    usuario = relationship("UsuarioORM", back_populates="refresh_tokens")


class AuditoriaLoginORM(Base):
    """Tabla de auditoría para intentos de login."""

    __tablename__ = "auditoria_login"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    exitoso = Column(Boolean, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    motivo = Column(Text, nullable=True)
    fecha = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
