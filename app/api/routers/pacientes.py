"""
Router para gestión de pacientes
"""

from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import PacienteCreate, PacienteResponse
from app.api.dependencies import get_paciente_repository, get_db, get_current_user
from app.api.policies import IntegrityPolicies
from app.api.exceptions import ResourceNotFoundException
from app.infra.repositories.paciente_repository import PacienteRepository
from app.domain.entities.usuarios import Paciente
from app.domain.value_objects.objetos_valor import Ubicacion

# DEMO ONLY IMPORT:
from app.infra.persistence.perfiles import SolicitanteORM

router = APIRouter()


@router.post("/", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def crear_paciente(
    data: PacienteCreate,
    repo: PacienteRepository = Depends(get_paciente_repository),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Crea un nuevo paciente en el sistema.

    POLICY APLICADA:
    - El solicitante que crea el paciente debe estar ACTIVO
    - Requiere autenticación
    - El solicitante_id se obtiene automáticamente del usuario autenticado

    El paciente estará asociado a un solicitante (usuario que gestiona sus turnos).
    El email/celular de contacto se obtienen del solicitante.
    """

    # Obtener el solicitante_id del usuario autenticado (perfil SolicitanteORM)
    solicitante = (
        db.query(SolicitanteORM)
        .filter(SolicitanteORM.usuario_id == current_user.id)
        .first()
    )

    if not solicitante:
        # DEMO ONLY: crear perfil solicitante si no existe
        if not getattr(current_user, "es_solicitante", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario no es un solicitante válido",
            )

        solicitante = SolicitanteORM(usuario_id=current_user.id)
        db.add(solicitante)
        db.flush()

    # Verificar si ya tiene un paciente (relación 1-1)
    if solicitante.paciente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Este solicitante ya tiene un paciente registrado. "
                "Solo se permite un paciente por solicitante."
            ),
        )

    policies = IntegrityPolicies()
    policies.validar_usuario_activo(db, current_user.id)

    ubicacion = Ubicacion(
        provincia=data.ubicacion.provincia,
        departamento=data.ubicacion.departamento,
        barrio=data.ubicacion.barrio,
        calle=data.ubicacion.calle,
        numero=data.ubicacion.numero,
        latitud=data.ubicacion.latitud,
        longitud=data.ubicacion.longitud,
    )

    paciente = Paciente(
        id=uuid4(),
        nombre=data.nombre,
        apellido=data.apellido,
        fecha_nacimiento=data.fecha_nacimiento,
        ubicacion=ubicacion,
        solicitante_id=solicitante.id,
        relacion=data.relacion,
        notas=data.notas or "",
    )

    paciente_creado = repo.crear(paciente, solicitante_id=solicitante.id)

    return paciente_creado


@router.get("/{paciente_id}", response_model=PacienteResponse)
def obtener_paciente(
    paciente_id: UUID,
    repo: PacienteRepository = Depends(get_paciente_repository),
    current_user=Depends(get_current_user),
):
    """
    Obtiene un paciente por su ID.
    Requiere autenticación.
    """
    paciente = repo.obtener_por_id(paciente_id)

    if not paciente:
        raise ResourceNotFoundException(f"Paciente con ID {paciente_id} no encontrado")

    return paciente


@router.get("/", response_model=List[PacienteResponse])
def listar_pacientes(
    solicitante_id: UUID = None,
    limite: int = 100,
    repo: PacienteRepository = Depends(get_paciente_repository),
):
    """
    Lista pacientes.

    - Si se proporciona solicitante_id, lista solo sus pacientes
    - Sino, lista todos los pacientes (con límite)
    """
    if solicitante_id:
        pacientes = repo.listar_por_solicitante(solicitante_id)
    else:
        pacientes = repo.listar_todos(limite=limite)

    return pacientes


@router.put("/{paciente_id}", response_model=PacienteResponse)
def actualizar_paciente(
    paciente_id: UUID,
    data: PacienteCreate,
    repo: PacienteRepository = Depends(get_paciente_repository),
):
    """
    Actualiza los datos de un paciente.
    """
    paciente = repo.obtener_por_id(paciente_id)

    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con ID {paciente_id} no encontrado",
        )

    try:
        paciente.nombre = data.nombre
        paciente.apellido = data.apellido
        paciente.fecha_nacimiento = data.fecha_nacimiento
        paciente.relacion = data.relacion
        paciente.notas = data.notas or ""

        if data.ubicacion:
            paciente.ubicacion = Ubicacion(
                provincia=data.ubicacion.provincia,
                departamento=data.ubicacion.departamento,
                barrio=data.ubicacion.barrio,
                calle=data.ubicacion.calle,
                numero=data.ubicacion.numero,
                latitud=data.ubicacion.latitud,
                longitud=data.ubicacion.longitud,
            )

        paciente_actualizado = repo.actualizar(paciente)

        if not paciente_actualizado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar paciente",
            )

        return paciente_actualizado

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_paciente(
    paciente_id: UUID,
    repo: PacienteRepository = Depends(get_paciente_repository),
):
    """
    Elimina un paciente (soft delete recomendado, hard delete implementado).
    """
    exito = repo.eliminar(paciente_id)

    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paciente con ID {paciente_id} no encontrado",
        )

    return None
