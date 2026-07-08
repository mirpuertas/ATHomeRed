"""
Router para gestión de consultas/citas médicas
"""

from typing import List
from uuid import UUID, uuid4
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import ConsultaCreate, ConsultaResponse, ConsultaUpdate
from app.api.dependencies import (
    get_consulta_repository,
    get_profesional_repository,
    get_paciente_repository,
    get_db,
    get_current_user,
)
from app.api.event_bus import get_event_bus
from app.api.policies import IntegrityPolicies
from app.api.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
    ForbiddenException,
    ConflictException,
)
from app.infra.repositories.consulta_repository import ConsultaRepository
from app.infra.repositories.profesional_repository import ProfesionalRepository
from app.infra.repositories.paciente_repository import PacienteRepository
from app.domain.entities.agenda import Cita
from app.domain.enumeraciones import EstadoCita
from app.domain.value_objects.objetos_valor import Ubicacion
from app.domain.eventos import (
    CitaCreada,
    CitaConfirmada,
    CitaCancelada,
    CitaCompletada,
    CitaReprogramada,
)
from app.domain.observers.observadores import EventBus, NotificadorEmail

router = APIRouter()


def _cita_to_response(cita: Cita) -> ConsultaResponse:
    """
    Adaptador Dominio → API.
    Mapea la entidad de dominio `Cita` al schema `ConsultaResponse`,
    alineando nombres de campos (motivo_consulta → motivo, creado_en → created_at).
    """
    return ConsultaResponse(
        id=cita.id,
        profesional_id=cita.profesional_id,
        paciente_id=cita.paciente_id,
        fecha=cita.fecha,
        hora_inicio=cita.hora_inicio,
        hora_fin=cita.hora_fin,
        estado=cita.estado.value,
        ubicacion=cita.ubicacion,
        motivo=cita.motivo_consulta or None,
        notas=cita.notas or None,
        created_at=cita.creado_en,
    )


@router.post("/", response_model=ConsultaResponse, status_code=status.HTTP_201_CREATED)
def crear_consulta(
    data: ConsultaCreate,
    repo: ConsultaRepository = Depends(get_consulta_repository),
    prof_repo: ProfesionalRepository = Depends(get_profesional_repository),
    pac_repo: PacienteRepository = Depends(get_paciente_repository),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    """
    Crea una nueva consulta/cita en estado PENDIENTE.

    Valida:
    - Profesional verificado y activo
    - Paciente pertenece al solicitante
    - Solicitante activo
    - Disponibilidad horaria (evita solapamientos)
    - Fecha y horarios válidos

    Publica evento CitaCreada en el EventBus para notificaciones.
    """
    try:
        policies = IntegrityPolicies()

        # POLICY 1: Validar que el profesional es VERIFICADO y ACTIVO
        profesional = prof_repo.obtener_por_id(data.profesional_id)
        if not profesional:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profesional con ID {data.profesional_id} no encontrado",
            )
        policies.validar_profesional_disponible(db, data.profesional_id)

        # POLICY 2: Validar que el paciente existe y pertenece al solicitante
        paciente = pac_repo.obtener_por_id(data.paciente_id)
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente con ID {data.paciente_id} no encontrado",
            )

        # POLICY 3: Validar que el solicitante que crea la cita es el dueño del paciente
        policies.validar_solicitante_es_dueno(db, data.paciente_id, data.solicitante_id)

        # POLICY 4: Validar que el solicitante está activo
        policies.validar_usuario_activo(db, data.solicitante_id)

        # VALIDACIONES DE NEGOCIO
        # Validación 1: Hora fin debe ser posterior a hora inicio
        if data.hora_fin <= data.hora_inicio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La hora de fin debe ser posterior a la hora de inicio",
            )

        # Validación 2: No permitir citas en fechas pasadas
        if data.fecha < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden crear consultas en fechas pasadas",
            )

        # Validación 3: Verificar disponibilidad (anti-double booking)
        consultas_existentes = repo.listar_por_profesional(
            profesional_id=data.profesional_id,
            desde=data.fecha,
            hasta=data.fecha,
            solo_activas=True,
        )

        for c in consultas_existentes:
            if (data.hora_inicio < c.hora_fin) and (data.hora_fin > c.hora_inicio):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El profesional no está disponible en el horario seleccionado",
                )

        ubicacion = Ubicacion(
            provincia=data.ubicacion.provincia,
            departamento=data.ubicacion.departamento,
            barrio=data.ubicacion.barrio,
            calle=data.ubicacion.calle,
            numero=data.ubicacion.numero,
            latitud=data.ubicacion.latitud,
            longitud=data.ubicacion.longitud,
        )

        cita = Cita(
            id=uuid4(),
            profesional_id=data.profesional_id,
            paciente_id=data.paciente_id,
            fecha=data.fecha,
            hora_inicio=data.hora_inicio,
            hora_fin=data.hora_fin,
            ubicacion=ubicacion,
            estado=EstadoCita.PENDIENTE,
            motivo_consulta=data.motivo or "",
            notas="",
        )

        cita_creada = repo.crear(cita)

        evento = CitaCreada(
            cita_id=cita_creada.id,
            profesional_id=data.profesional_id,
            paciente_id=data.paciente_id,
            solicitante_id=data.solicitante_id,
        )
        event_bus.publicar(evento)

        return _cita_to_response(cita_creada)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (
        BusinessRuleException,
        ResourceNotFoundException,
        ForbiddenException,
        ConflictException,
    ):
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear consulta: {str(e)}",
        )


@router.get("/{consulta_id}", response_model=ConsultaResponse)
def obtener_consulta(
    consulta_id: UUID,
    repo: ConsultaRepository = Depends(get_consulta_repository),
):
    """
    Obtiene una consulta por su ID.
    """
    consulta = repo.obtener_por_id(consulta_id)

    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta con ID {consulta_id} no encontrada",
        )

    return _cita_to_response(consulta)


@router.get("/profesional/{profesional_id}", response_model=List[ConsultaResponse])
def listar_consultas_profesional(
    profesional_id: UUID,
    desde: date = None,
    hasta: date = None,
    solo_activas: bool = False,
    repo: ConsultaRepository = Depends(get_consulta_repository),
):
    """
    Lista todas las consultas de un profesional.

    - desde: Fecha inicial (opcional)
    - hasta: Fecha final (opcional)
    - solo_activas: Si True, excluye canceladas y completadas
    """
    consultas = repo.listar_por_profesional(
        profesional_id, desde=desde, hasta=hasta, solo_activas=solo_activas
    )

    return [_cita_to_response(c) for c in consultas]


@router.get("/paciente/{paciente_id}", response_model=List[ConsultaResponse])
def listar_consultas_paciente(
    paciente_id: UUID,
    desde: date = None,
    solo_activas: bool = False,
    repo: ConsultaRepository = Depends(get_consulta_repository),
):
    """
    Lista todas las consultas de un paciente.

    - desde: Fecha inicial (opcional)
    - solo_activas: Si True, excluye canceladas y completadas
    """
    consultas = repo.listar_por_paciente(
        paciente_id, desde=desde, solo_activas=solo_activas
    )

    return [_cita_to_response(c) for c in consultas]


@router.put("/{consulta_id}", response_model=ConsultaResponse)
def actualizar_consulta(
    consulta_id: UUID,
    data: ConsultaUpdate,
    repo: ConsultaRepository = Depends(get_consulta_repository),
):
    """
    Actualiza una consulta existente.
    Solo permite actualizar fecha, horarios y notas si la consulta no está completada/cancelada.
    """
    consulta = repo.obtener_por_id(consulta_id)

    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta con ID {consulta_id} no encontrada",
        )

    if not consulta.puede_modificarse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede modificar una consulta en estado {consulta.estado.value}",
        )

    try:
        if data.fecha:
            consulta.fecha = data.fecha
        if data.hora_inicio:
            consulta.hora_inicio = data.hora_inicio
        if data.hora_fin:
            consulta.hora_fin = data.hora_fin
        if data.motivo:
            consulta.motivo_consulta = data.motivo
        if data.notas:
            consulta.notas = data.notas

        consulta_actualizada = repo.actualizar(consulta)

        if not consulta_actualizada:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar consulta",
            )

        return _cita_to_response(consulta_actualizada)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{consulta_id}/confirmar", response_model=ConsultaResponse)
def confirmar_consulta(
    consulta_id: UUID,
    repo: ConsultaRepository = Depends(get_consulta_repository),
    event_bus: EventBus = Depends(get_event_bus),
    current_user=Depends(get_current_user),
):
    """
    Confirma una consulta pendiente.

    **Requiere autenticación**: Paciente o Profesional pueden confirmar.

    - **Paciente**: Puede confirmar si es el dueño de la cita
    - **Profesional**: Puede confirmar si es el asignado a la cita

    Cuando se confirma:
    1. Valida que la cita le pertenezca al usuario autenticado
    2. Adjunta el NotificadorEmail (Observer) para enviar notificaciones
    3. Cambia el estado a CONFIRMADA
    4. Publica evento CitaConfirmada con el ID y rol del confirmante

    El Observer enviará automáticamente emails a ambas partes.
    """
    consulta = repo.obtener_por_id(consulta_id)

    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta con ID {consulta_id} no encontrada",
        )

    es_paciente = consulta.paciente_id == current_user.id
    es_profesional = consulta.profesional_id == current_user.id

    if not (es_paciente or es_profesional):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para confirmar esta consulta.",
        )

    try:
        notificador = NotificadorEmail()
        consulta.attach(notificador)

        rol = "paciente" if es_paciente else "profesional"
        confirmado_por = f"{rol}:{current_user.id}"

        consulta.confirmar(confirmado_por=confirmado_por)

        consulta_actualizada = repo.actualizar(consulta)

        evento = CitaConfirmada(cita_id=consulta_id, confirmado_por=confirmado_por)
        event_bus.publicar(evento)

        return _cita_to_response(consulta_actualizada)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{consulta_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_consulta(
    consulta_id: UUID,
    motivo: str = None,
    repo: ConsultaRepository = Depends(get_consulta_repository),
    event_bus: EventBus = Depends(get_event_bus),
    current_user=Depends(get_current_user),
):
    """
    Cancela una consulta.

    **Requiere autenticación**: Paciente o Profesional pueden cancelar.

    - **Paciente**: Puede cancelar si es el dueño de la cita
    - **Profesional**: Puede cancelar si es el asignado a la cita

    El Observer enviará notificaciones automáticas a ambas partes.
    """
    consulta = repo.obtener_por_id(consulta_id)

    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta con ID {consulta_id} no encontrada",
        )

    es_paciente = consulta.paciente_id == current_user.id
    es_profesional = consulta.profesional_id == current_user.id

    if not (es_paciente or es_profesional):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cancelar esta consulta.",
        )

    try:
        notificador = NotificadorEmail()
        consulta.attach(notificador)

        rol = "paciente" if es_paciente else "profesional"
        cancelado_por = f"{rol}:{current_user.id}"

        consulta.cancelar(motivo=motivo, cancelado_por=cancelado_por)
        repo.actualizar(consulta)

        evento = CitaCancelada(
            cita_id=consulta_id, motivo=motivo, cancelado_por=cancelado_por
        )
        event_bus.publicar(evento)

        return None

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{consulta_id}/completar", response_model=ConsultaResponse)
def completar_consulta(
    consulta_id: UUID,
    notas_finales: str = None,
    repo: ConsultaRepository = Depends(get_consulta_repository),
    event_bus: EventBus = Depends(get_event_bus),
    current_user=Depends(get_current_user),
):
    """
    Marca una consulta confirmada como completada.

    **Requiere autenticación**: Solo el **Profesional** puede completar.

    El profesional completa la cita después de brindar el servicio.
    El Observer enviará notificaciones al paciente confirmando la finalización.
    """
    consulta = repo.obtener_por_id(consulta_id)

    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta con ID {consulta_id} no encontrada",
        )

    if consulta.profesional_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el profesional asignado puede completar esta consulta.",
        )

    try:
        notificador = NotificadorEmail()
        consulta.attach(notificador)

        consulta.completar(notas_finales=notas_finales)
        consulta_actualizada = repo.actualizar(consulta)

        evento = CitaCompletada(cita_id=consulta_id, notas=notas_finales)
        event_bus.publicar(evento)

        return _cita_to_response(consulta_actualizada)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{consulta_id}/reprogramar", response_model=ConsultaResponse)
def reprogramar_consulta(
    consulta_id: UUID,
    data: ConsultaUpdate,
    repo: ConsultaRepository = Depends(get_consulta_repository),
    event_bus: EventBus = Depends(get_event_bus),
    current_user=Depends(get_current_user),
):
    """
    Reprograma una consulta (cambia fecha y horarios).

    **Requiere autenticación**: Paciente o Profesional pueden reprogramar.

    - **Paciente**: Puede reprogramar si es el dueño de la cita
    - **Profesional**: Puede reprogramar si es el asignado a la cita

    El Observer enviará notificaciones a ambas partes con el nuevo horario.
    """
    consulta = repo.obtener_por_id(consulta_id)

    if not consulta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consulta con ID {consulta_id} no encontrada",
        )

    if not data.fecha or not data.hora_inicio or not data.hora_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Para reprogramar se requiere fecha, hora_inicio y hora_fin",
        )

    es_paciente = consulta.paciente_id == current_user.id
    es_profesional = consulta.profesional_id == current_user.id

    if not (es_paciente or es_profesional):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para reprogramar esta consulta.",
        )

    try:
        fecha_anterior = f"{consulta.fecha} {consulta.hora_inicio}-{consulta.hora_fin}"

        notificador = NotificadorEmail()
        consulta.attach(notificador)

        consulta.reprogramar(
            nueva_fecha=data.fecha,
            nueva_hora_inicio=data.hora_inicio,
            nueva_hora_fin=data.hora_fin,
        )
        consulta_actualizada = repo.actualizar(consulta)

        fecha_nueva = f"{data.fecha} {data.hora_inicio}-{data.hora_fin}"
        evento = CitaReprogramada(
            cita_id=consulta_id,
            fecha_anterior=fecha_anterior,
            fecha_nueva=fecha_nueva,
        )
        event_bus.publicar(evento)

        return _cita_to_response(consulta_actualizada)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
