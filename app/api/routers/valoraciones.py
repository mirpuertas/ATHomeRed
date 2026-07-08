"""
Router para gestión de valoraciones
"""

from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import (
    ValoracionCreate,
    ValoracionResponse,
    PromedioValoracionResponse,
)
from app.api.dependencies import (
    get_valoracion_repository,
    get_profesional_repository,
    get_paciente_repository,
    get_current_user,
)
from app.infra.repositories.valoracion_repository import ValoracionRepository
from app.infra.repositories.profesional_repository import ProfesionalRepository
from app.infra.repositories.paciente_repository import PacienteRepository
from app.domain.entities.valoraciones import Valoracion
from datetime import datetime, timezone

router = APIRouter()


@router.post(
    "/", response_model=ValoracionResponse, status_code=status.HTTP_201_CREATED
)
def crear_valoracion(
    data: ValoracionCreate,
    repo: ValoracionRepository = Depends(get_valoracion_repository),
    prof_repo: ProfesionalRepository = Depends(get_profesional_repository),
    pac_repo: PacienteRepository = Depends(get_paciente_repository),
):
    """
    Crea una nueva valoración de un paciente hacia un profesional.

    - Valida que el profesional existe
    - Valida que el paciente existe
    - Verifica que no exista ya una valoración previa (opcional)
    """
    try:
        profesional = prof_repo.obtener_por_id(data.profesional_id)
        if not profesional:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profesional con ID {data.profesional_id} no encontrado",
            )

        paciente = pac_repo.obtener_por_id(data.paciente_id)
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente con ID {data.paciente_id} no encontrado",
            )

        if repo.existe_valoracion(data.profesional_id, data.paciente_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El paciente ya ha valorado a este profesional",
            )

        valoracion = Valoracion(
            id=uuid4(),
            id_profesional=data.profesional_id,
            id_paciente=data.paciente_id,
            puntuacion=data.puntuacion,
            comentario=data.comentario,
            fecha=datetime.now(timezone.utc),
        )

        valoracion_creada = repo.crear(valoracion)

        return valoracion_creada

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear valoración: {str(e)}",
        )


@router.get("/profesional/{profesional_id}", response_model=List[ValoracionResponse])
def listar_valoraciones_profesional(
    profesional_id: UUID,
    limite: int = 100,
    repo: ValoracionRepository = Depends(get_valoracion_repository),
):
    """
    Lista las valoraciones de un profesional.
    Ordenadas por fecha descendente (más recientes primero).
    """
    valoraciones = repo.listar_por_profesional(profesional_id, limite=limite)
    return valoraciones


@router.get(
    "/profesional/{profesional_id}/promedio",
    response_model=PromedioValoracionResponse,
)
def obtener_promedio_profesional(
    profesional_id: UUID,
    repo: ValoracionRepository = Depends(get_valoracion_repository),
):
    """
    Obtiene el promedio de valoraciones de un profesional.
    """
    promedio = repo.obtener_promedio_profesional(profesional_id)
    total = repo.contar_por_profesional(profesional_id)

    return PromedioValoracionResponse(
        profesional_id=profesional_id,
        promedio=promedio,
        total_valoraciones=total,
    )


@router.get("/paciente/{paciente_id}", response_model=List[ValoracionResponse])
def listar_valoraciones_paciente(
    paciente_id: UUID,
    limite: int = 100,
    repo: ValoracionRepository = Depends(get_valoracion_repository),
):
    """
    Lista las valoraciones hechas por un paciente.
    """
    valoraciones = repo.listar_por_paciente(paciente_id, limite=limite)
    return valoraciones


@router.get("/{valoracion_id}", response_model=ValoracionResponse)
def obtener_valoracion(
    valoracion_id: UUID,
    repo: ValoracionRepository = Depends(get_valoracion_repository),
):
    """
    Obtiene una valoración específica por su ID.
    """
    valoracion = repo.obtener_por_id(valoracion_id)

    if not valoracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Valoración con ID {valoracion_id} no encontrada",
        )

    return valoracion


@router.delete("/{valoracion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_valoracion(
    valoracion_id: UUID,
    repo: ValoracionRepository = Depends(get_valoracion_repository),
    current_user=Depends(get_current_user),
):
    """
    Elimina una valoración.

    Solo el paciente que creó la valoración puede eliminarla.
    Requiere autenticación (Bearer token).
    """
    valoracion = repo.obtener_por_id(valoracion_id)

    if not valoracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Valoración con ID {valoracion_id} no encontrada",
        )

    if valoracion.id_paciente != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar esta valoración",
        )

    exito = repo.eliminar(valoracion_id)

    if not exito:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar la valoración",
        )

    return None
