"""
Router para gestión de profesionales
"""

from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import (
    ProfesionalCreate,
    ProfesionalResponse,
    ProfesionalUpdate,
)
from app.api.dependencies import (
    get_profesional_repository,
    get_catalogo_repository,
    get_current_user,
)
from app.api.exceptions import ResourceNotFoundException
from app.infra.repositories.profesional_repository import ProfesionalRepository
from app.infra.repositories.catalogo_repository import CatalogoRepository
from app.domain.entities.usuarios import Profesional
from app.domain.value_objects.objetos_valor import (
    Ubicacion,
    Disponibilidad,
    Matricula,
)
from app.domain.enumeraciones import DiaSemana

router = APIRouter()


@router.post(
    "/",
    response_model=ProfesionalResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_profesional(
    data: ProfesionalCreate,
    repo: ProfesionalRepository = Depends(get_profesional_repository),
    catalogo_repo: CatalogoRepository = Depends(get_catalogo_repository),
    current_user=Depends(get_current_user),
):
    """
    Crea un nuevo profesional en el sistema.
    Requiere autenticación.
    """
    ubicacion = Ubicacion(
        provincia=data.ubicacion.provincia,
        departamento=data.ubicacion.departamento,
        barrio=data.ubicacion.barrio,
        calle=data.ubicacion.calle,
        numero=data.ubicacion.numero,
        latitud=data.ubicacion.latitud,
        longitud=data.ubicacion.longitud,
    )

    especialidades = []
    for esp_id in data.especialidades:
        especialidad = catalogo_repo.obtener_especialidad_por_id(esp_id)
        if not especialidad:
            raise ResourceNotFoundException(
                f"Especialidad con ID {esp_id} no encontrada"
            )
        especialidades.append(especialidad)

        disponibilidades = [
            Disponibilidad(
                dias_semana=[DiaSemana(d) for d in disp.dias_semana],
                hora_inicio=disp.hora_inicio,
                hora_fin=disp.hora_fin,
            )
            for disp in (data.disponibilidades or [])
        ]

        matriculas = [
            Matricula(
                numero=mat.numero,
                provincia=mat.provincia,
                vigente_desde=mat.vigente_desde,
                vigente_hasta=mat.vigente_hasta,
            )
            for mat in (data.matriculas or [])
        ]

        profesional = Profesional(
            id=uuid4(),
            nombre=data.nombre,
            apellido=data.apellido,
            email=data.email,
            celular=data.celular or "",
            ubicacion=ubicacion,
            activo=True,
            verificado=False,
            especialidades=especialidades,
            disponibilidades=disponibilidades,
            matriculas=matriculas,
        )

        # Vinculamos el profesional al usuario autenticado para que el flujo de demo
        # quede consistente (un usuario ↔ un perfil profesional).
        profesional_creado = repo.crear(profesional, usuario_id=current_user.id)

        return profesional_creado


@router.get("/{profesional_id}", response_model=ProfesionalResponse)
def obtener_profesional(
    profesional_id: UUID,
    repo: ProfesionalRepository = Depends(get_profesional_repository),
    current_user=Depends(get_current_user),
):
    """
    Obtiene un profesional por su ID.
    Requiere autenticación.
    """
    profesional = repo.obtener_por_id(profesional_id)

    if not profesional:
        raise ResourceNotFoundException(
            f"Profesional con ID {profesional_id} no encontrado"
        )

    return profesional


@router.get("/", response_model=List[ProfesionalResponse])
def listar_profesionales(
    solo_activos: bool = True,
    repo: ProfesionalRepository = Depends(get_profesional_repository),
):
    """
    Lista todos los profesionales activos.
    """
    if solo_activos:
        profesionales = repo.listar_activos()
    else:
        profesionales = repo.listar_todos()

    return profesionales


@router.put("/{profesional_id}", response_model=ProfesionalResponse)
def actualizar_profesional(
    profesional_id: UUID,
    data: ProfesionalUpdate,
    repo: ProfesionalRepository = Depends(get_profesional_repository),
    catalogo_repo: CatalogoRepository = Depends(get_catalogo_repository),
):
    """
    Actualiza los datos de un profesional.
    """
    profesional = repo.obtener_por_id(profesional_id)

    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profesional con ID {profesional_id} no encontrado",
        )

    if data.nombre is not None:
        profesional.nombre = data.nombre
    if data.apellido is not None:
        profesional.apellido = data.apellido
    if data.celular is not None:
        profesional.celular = data.celular

    if data.ubicacion is not None:
        profesional.ubicacion = Ubicacion(
            provincia=data.ubicacion.provincia,
            departamento=data.ubicacion.departamento,
            barrio=data.ubicacion.barrio,
            calle=data.ubicacion.calle,
            numero=data.ubicacion.numero,
            latitud=data.ubicacion.latitud,
            longitud=data.ubicacion.longitud,
        )

    if data.especialidades is not None:
        especialidades = []
        for esp_id in data.especialidades:
            especialidad = catalogo_repo.obtener_especialidad_por_id(esp_id)
            if not especialidad:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Especialidad con ID {esp_id} no encontrada",
                )
            especialidades.append(especialidad)
        profesional.especialidades = especialidades

    if data.disponibilidades is not None:
        profesional.disponibilidades = [
            Disponibilidad(
                dias_semana=[DiaSemana(d) for d in disp.dias_semana],
                hora_inicio=disp.hora_inicio,
                hora_fin=disp.hora_fin,
            )
            for disp in data.disponibilidades
        ]

    profesional_actualizado = repo.actualizar(profesional)

    return profesional_actualizado


@router.delete("/{profesional_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_profesional(
    profesional_id: UUID,
    repo: ProfesionalRepository = Depends(get_profesional_repository),
):
    """
    Desactiva un profesional (soft delete).
    """
    profesional = repo.obtener_por_id(profesional_id)

    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profesional con ID {profesional_id} no encontrado",
        )

    repo.desactivar(profesional_id)

    return None


@router.post("/{profesional_id}/verificar", response_model=ProfesionalResponse)
def verificar_profesional(
    profesional_id: UUID,
    repo: ProfesionalRepository = Depends(get_profesional_repository),
):
    """
    Marca un profesional como verificado.

    NOTA: En producción agregar: current_user = Depends(get_current_user)
          y validar que sea admin.
    """
    profesional = repo.obtener_por_id(profesional_id)

    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profesional con ID {profesional_id} no encontrado",
        )

    profesional_verificado = repo.verificar(profesional_id)

    return profesional_verificado
