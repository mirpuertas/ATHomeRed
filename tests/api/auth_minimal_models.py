"""
Modelos mínimos para test de auth API flow (sin FKs ni esquema).
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class UsuarioORM(Base):
    __tablename__ = "usuario"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    celular = Column(String(50))
    es_solicitante = Column(Boolean, default=True, nullable=False)
    es_profesional = Column(Boolean, default=False, nullable=False)
    password_hash = Column(String(255))
    ultimo_login = Column(DateTime)
    intentos_fallidos = Column(Integer, default=0, nullable=False)
    bloqueado_hasta = Column(DateTime)
    activo = Column(Boolean, default=True, nullable=False)
    verificado = Column(Boolean, default=False, nullable=False)


class RefreshTokenORM(Base):
    __tablename__ = "refresh_tokens"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id = Column(String(36), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expira_en = Column(DateTime, nullable=False)
    revocado = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditoriaLoginORM(Base):
    __tablename__ = "auditoria_login"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    exitoso = Column(Boolean, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    motivo = Column(Text)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
