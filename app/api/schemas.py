"""
Pydantic schemas para validación de requests/responses
Estos son los DTOs (Data Transfer Objects) de la API
"""

from datetime import date, time, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UbicacionSchema(BaseModel):
    """Schema para ubicación"""

    provincia: str
    departamento: str
    barrio: str
    calle: str
    numero: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class DisponibilidadSchema(BaseModel):
    """Schema para disponibilidad horaria"""

    dias_semana: List[int] = Field(
        description="Lista de días (1=Lunes, 7=Domingo) - ISO 8601"
    )
    hora_inicio: time
    hora_fin: time

    model_config = ConfigDict(from_attributes=True)


class MatriculaSchema(BaseModel):
    """Schema para matrícula profesional"""

    numero: str
    provincia: str
    vigente_desde: date
    vigente_hasta: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class EspecialidadSchema(BaseModel):
    """Schema para especialidad médica"""

    id: int
    nombre: str
    tarifa: Decimal

    model_config = ConfigDict(from_attributes=True)


class UsuarioBase(BaseModel):
    """Schema base para usuarios"""

    nombre: str = Field(min_length=2, max_length=50)
    apellido: str = Field(min_length=2, max_length=50)
    email: EmailStr
    celular: Optional[str] = Field(None, max_length=20)


class ProfesionalCreate(UsuarioBase):
    """Schema para crear un profesional"""

    ubicacion: UbicacionSchema
    especialidades: List[int] = Field(description="IDs de especialidades")
    disponibilidades: Optional[List[DisponibilidadSchema]] = None
    matriculas: Optional[List[MatriculaSchema]] = None


class ProfesionalResponse(UsuarioBase):
    """Schema para respuesta de profesional"""

    id: UUID
    ubicacion: UbicacionSchema
    activo: bool
    verificado: bool
    especialidades: List[EspecialidadSchema]
    disponibilidades: List[DisponibilidadSchema]
    matriculas: List[MatriculaSchema]

    model_config = ConfigDict(from_attributes=True)


class ProfesionalUpdate(BaseModel):
    """Schema para actualizar profesional"""

    nombre: Optional[str] = None
    apellido: Optional[str] = None
    celular: Optional[str] = None
    ubicacion: Optional[UbicacionSchema] = None
    especialidades: Optional[List[int]] = None
    disponibilidades: Optional[List[DisponibilidadSchema]] = None


class PacienteCreate(BaseModel):
    """Schema para crear paciente (sin email/celular - los tiene el Solicitante)"""

    nombre: str = Field(min_length=2, max_length=50)
    apellido: str = Field(min_length=2, max_length=50)
    fecha_nacimiento: date
    relacion: str = Field(
        default="Yo mismo",
        description="Relación con el solicitante. Ejemplos: 'Yo mismo', 'Madre', 'Padre', 'Hijo', 'Hija', 'Hermano', 'Hermana', 'Esposo', 'Esposa', 'Abuelo', 'Abuela', 'Tío', 'Tía', 'Tutor/a', 'Otro familiar'",
    )
    notas: Optional[str] = None
    ubicacion: UbicacionSchema


class PacienteResponse(BaseModel):
    """Schema para respuesta de paciente"""

    id: UUID
    nombre: str
    apellido: str
    fecha_nacimiento: date
    relacion: str
    notas: Optional[str]
    ubicacion: UbicacionSchema
    solicitante_id: UUID

    @property
    def edad(self) -> int:
        today = date.today()
        years = today.year - self.fecha_nacimiento.year
        if (today.month, today.day) < (
            self.fecha_nacimiento.month,
            self.fecha_nacimiento.day,
        ):
            years -= 1
        return years

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    model_config = ConfigDict(from_attributes=True)


class ConsultaCreate(BaseModel):
    """Schema para crear una consulta"""

    profesional_id: UUID
    paciente_id: UUID
    solicitante_id: UUID
    fecha: date
    hora_inicio: time
    hora_fin: time
    ubicacion: UbicacionSchema
    motivo: Optional[str] = None


class ConsultaResponse(BaseModel):
    """Schema para respuesta de consulta"""

    id: UUID
    profesional_id: UUID
    paciente_id: UUID
    fecha: date
    hora_inicio: time
    hora_fin: time
    estado: str
    ubicacion: UbicacionSchema
    motivo: Optional[str]
    notas: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultaUpdate(BaseModel):
    """Schema para actualizar consulta"""

    fecha: Optional[date] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    motivo: Optional[str] = None
    notas: Optional[str] = None


class BusquedaProfesionalRequest(BaseModel):
    """Schema para búsqueda de profesionales"""

    especialidad_id: Optional[int] = None
    nombre_especialidad: Optional[str] = None
    provincia: Optional[str] = None
    departamento: Optional[str] = None
    barrio: Optional[str] = None
    dia_semana: Optional[int] = Field(
        None, ge=1, le=7, description="1=Lunes, 7=Domingo (ISO 8601)"
    )
    solo_verificados: bool = True
    solo_activos: bool = True


class BusquedaProfesionalResponse(BaseModel):
    """Schema para resultado de búsqueda"""

    profesionales: List[ProfesionalResponse]
    total: int
    criterios_aplicados: dict


class ValoracionCreate(BaseModel):
    """Schema para crear valoración"""

    profesional_id: UUID
    paciente_id: UUID
    puntuacion: int = Field(ge=1, le=5, description="Puntuación de 1 a 5 estrellas")
    comentario: Optional[str] = Field(None, max_length=500)


class ValoracionResponse(BaseModel):
    """Schema para respuesta de valoración"""

    id: UUID
    profesional_id: UUID
    paciente_id: UUID
    puntuacion: int
    comentario: Optional[str]
    fecha: date

    model_config = ConfigDict(from_attributes=True)


class PromedioValoracionResponse(BaseModel):
    """Schema para promedio de valoraciones de un profesional"""

    profesional_id: UUID
    promedio: float
    total_valoraciones: int


class TokenSchema(BaseModel):
    """Schema para token de autenticación"""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Schema para login"""

    email: EmailStr
    password: str


class RegisterRequest(UsuarioBase):
    """Schema para registro"""

    password: str = Field(min_length=8)
    es_profesional: bool = False
    es_solicitante: bool = True
