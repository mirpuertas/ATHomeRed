"""
Router para búsqueda de profesionales
Implementa las estrategias de búsqueda del dominio
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.api.schemas import (
    BusquedaProfesionalRequest,
    BusquedaProfesionalResponse,
)
from app.api.dependencies import (
    get_profesional_repository,
    get_direccion_repository,
    get_catalogo_repository,
)
from app.api.exceptions import ResourceNotFoundException, BusinessRuleException
from app.infra.repositories.profesional_repository import ProfesionalRepository
from app.infra.repositories.direccion_repository import DireccionRepository
from app.infra.repositories.catalogo_repository import CatalogoRepository

from app.domain.entities.catalogo import FiltroBusqueda
from app.domain.strategies.buscador import Buscador
from app.domain.strategies.estrategia import (
    BusquedaPorZona,
    BusquedaPorEspecialidad,
    BusquedaCombinada,
)

router = APIRouter()


@router.post("/profesionales", response_model=BusquedaProfesionalResponse)
def buscar_profesionales(
    criterios: BusquedaProfesionalRequest,
    repo: ProfesionalRepository = Depends(get_profesional_repository),
    catalogo_repo: CatalogoRepository = Depends(get_catalogo_repository),
):
    """
    Busca profesionales según múltiples criterios.

    Utiliza el patrón Strategy del dominio para aplicar filtros:
    - Por especialidad (ID o nombre - se valida que exista)
    - Por ubicación (provincia/departamento/barrio)
    - Por disponibilidad (día de la semana)
    - Solo verificados/activos
    """

    if criterios.departamento and not criterios.provincia:
        raise BusinessRuleException(
            "Se debe especificar la provincia si se indica el departamento."
        )

    if criterios.barrio and not criterios.departamento:
        raise BusinessRuleException(
            "Se debe especificar el departamento si se indica el barrio."
        )

    especialidad_id = criterios.especialidad_id
    especialidad_nombre = criterios.nombre_especialidad

    if especialidad_nombre and not especialidad_id:
        especialidad = catalogo_repo.obtener_especialidad_por_nombre(
            especialidad_nombre
        )
        if especialidad:
            especialidad_id = especialidad.id
        else:
            raise ResourceNotFoundException(
                f"No se encontró la especialidad '{especialidad_nombre}'"
            )

    if especialidad_id:
        especialidad = catalogo_repo.obtener_especialidad_por_id(especialidad_id)
        if not especialidad:
            raise ResourceNotFoundException(
                f"No existe la especialidad con ID {especialidad_id}"
            )
        especialidad_nombre = especialidad.nombre

    filtro = FiltroBusqueda(
        id_especialidad=especialidad_id,
        nombre_especialidad=especialidad_nombre,
        provincia=criterios.provincia,
        departamento=criterios.departamento,
        barrio=criterios.barrio,
    )

    if (filtro.id_especialidad or filtro.nombre_especialidad) and (
        filtro.provincia or filtro.departamento or filtro.barrio
    ):
        estrategia = BusquedaCombinada()
    elif filtro.id_especialidad or filtro.nombre_especialidad:
        estrategia = BusquedaPorEspecialidad()
    elif filtro.provincia or filtro.departamento or filtro.barrio:
        estrategia = BusquedaPorZona()
    else:
        raise BusinessRuleException(
            "Se debe especificar un criterio de búsqueda válido."
        )

    buscador = Buscador(repo, estrategia)
    profesionales = buscador.buscar(filtro)

    return BusquedaProfesionalResponse(
        profesionales=profesionales,
        total=len(profesionales),
        criterios_aplicados=filtro.__dict__,
    )


@router.get("/especialidades")
def listar_especialidades(
    repo: CatalogoRepository = Depends(get_catalogo_repository),
):
    """
    Lista todas las especialidades disponibles desde la base de datos.
    """
    especialidades = repo.listar_especialidades()
    return {
        "especialidades": [
            {"id": esp.id, "nombre": esp.nombre} for esp in especialidades
        ]
    }


@router.get("/ubicaciones/provincias")
def listar_provincias(
    repo: DireccionRepository = Depends(get_direccion_repository),
):
    """
    Lista todas las provincias disponibles desde la base de datos.
    """
    provincias = repo.listar_provincias()
    return {
        "provincias": [
            {"id": str(provincia.id), "nombre": provincia.nombre}
            for provincia in provincias
        ]
    }


@router.get("/ubicaciones/provincias/{provincia_id}/departamentos")
def listar_departamentos(
    provincia_id: UUID,
    repo: DireccionRepository = Depends(get_direccion_repository),
):
    """
    Lista todos los departamentos de una provincia específica.
    """
    try:
        departamentos = repo.listar_departamentos(provincia_id)
        return {
            "departamentos": [
                {"id": str(depto.id), "nombre": depto.nombre} for depto in departamentos
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar departamentos: {str(e)}",
        )


@router.get("/ubicaciones/departamentos/{departamento_id}/barrios")
def listar_barrios(
    departamento_id: UUID,
    repo: DireccionRepository = Depends(get_direccion_repository),
):
    """
    Lista todos los barrios de un departamento específico.
    """
    try:
        barrios = repo.listar_barrios(departamento_id)
        return {
            "barrios": [
                {"id": str(barrio.id), "nombre": barrio.nombre} for barrio in barrios
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar barrios: {str(e)}",
        )
