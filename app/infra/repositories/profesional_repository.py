from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import unicodedata

from app.domain.entities.usuarios import Profesional
from app.domain.entities.catalogo import Especialidad
from app.domain.value_objects.objetos_valor import (
    Ubicacion,
    Disponibilidad,
    Matricula,
)
from app.domain.enumeraciones import DiaSemana
from app.infra.persistence.perfiles import ProfesionalORM
from app.infra.persistence.usuarios import UsuarioORM
from app.infra.persistence.servicios import EspecialidadORM
from app.infra.persistence.ubicacion import (
    DireccionORM,
    BarrioORM,
    DepartamentoORM,
    ProvinciaORM,
)


from app.infra.repositories.direccion_repository import DireccionRepository

DIAS_NOMBRE_A_NUMERO = {
    "lunes": DiaSemana.LUNES,
    "martes": DiaSemana.MARTES,
    "miercoles": DiaSemana.MIERCOLES,
    "jueves": DiaSemana.JUEVES,
    "viernes": DiaSemana.VIERNES,
    "sabado": DiaSemana.SABADO,
    "domingo": DiaSemana.DOMINGO,
}


def _normalizar_texto(texto: str) -> str:
    """Normaliza texto removiendo acentos y convirtiendo a minúsculas"""
    nfkd = unicodedata.normalize("NFD", texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()


class ProfesionalRepository:
    def __init__(self, session: Session):
        self.session = session
        self.direccion_repo = DireccionRepository(session)

    def _convertir_dia_a_enum(self, dia: str) -> DiaSemana:
        """
        Convierte un día en formato texto o número a DiaSemana enum.
        Soporta nombres de días en español (con o sin acentos) y números (1-7).
        """
        dia_limpio = dia.strip()

        if dia_limpio.isdigit():
            return DiaSemana(int(dia_limpio))

        dia_normalizado = _normalizar_texto(dia_limpio)

        if dia_normalizado in DIAS_NOMBRE_A_NUMERO:
            return DIAS_NOMBRE_A_NUMERO[dia_normalizado]

        raise ValueError(
            f"Día no válido: '{dia}'. Debe ser un nombre de día en español o un número entre 1 y 7."
        )

    def _to_domain(self, orm: ProfesionalORM) -> Profesional:
        """ORM → Dominio"""
        ubicacion = None
        if orm.direccion:
            ubicacion = Ubicacion(
                provincia=orm.direccion.barrio.departamento.provincia.nombre,
                departamento=orm.direccion.barrio.departamento.nombre,
                barrio=orm.direccion.barrio.nombre,
                calle=orm.direccion.calle,
                numero=str(orm.direccion.numero),
                latitud=orm.direccion.latitud,
                longitud=orm.direccion.longitud,
            )

        if ubicacion is None:
            ubicacion = Ubicacion(
                provincia="", departamento="", barrio="", calle="", numero=""
            )

        return Profesional(
            id=orm.id,
            nombre=orm.usuario.nombre,
            apellido=orm.usuario.apellido,
            email=orm.usuario.email,
            celular=orm.usuario.celular or "",
            ubicacion=ubicacion,
            activo=orm.activo,
            verificado=orm.verificado,
            especialidades=[
                Especialidad(id=e.id_especialidad, nombre=e.nombre, tarifa=e.tarifa)
                for e in (orm.especialidades or [])
            ],
            disponibilidades=[
                Disponibilidad(
                    dias_semana=[
                        self._convertir_dia_a_enum(d)
                        for d in disp.dias_semana
                        if d and d.strip()
                    ],
                    hora_inicio=disp.hora_inicio,
                    hora_fin=disp.hora_fin,
                )
                for disp in (orm.disponibilidades or [])
            ],
            matriculas=[
                Matricula(
                    numero=m.nro_matricula,
                    provincia=m.provincia.nombre,
                    vigente_desde=m.vigente_desde,
                    vigente_hasta=m.vigente_hasta,
                )
                for m in (orm.matriculas or [])
            ],
        )

    def obtener_por_id(self, id: UUID) -> Optional[Profesional]:
        orm = (
            self.session.query(ProfesionalORM)
            .filter(ProfesionalORM.id == str(id))
            .first()
        )
        return self._to_domain(orm) if orm else None

    def listar_activos(self) -> List[Profesional]:
        """Para Strategy de búsqueda"""
        orms = self.session.query(ProfesionalORM).filter(ProfesionalORM.activo).all()
        return [self._to_domain(orm) for orm in orms]

    def listar_todos(self) -> List[Profesional]:
        orms = self.session.query(ProfesionalORM).all()
        return [self._to_domain(orm) for orm in orms]

    def crear(
        self,
        profesional: Profesional,
        usuario_id: Optional[UUID] = None,
        direccion_id: Optional[UUID] = None,
    ) -> Profesional:
        """
        Guarda nuevo profesional (dominio → ORM)

        Args:
            profesional: Entidad de dominio Profesional
            usuario_id: (Opcional) ID de usuario existente.
                       Si no se proporciona, se crea un nuevo UsuarioORM.
            direccion_id: (Opcional) ID de dirección existente.
                         Si no se proporciona y el profesional tiene ubicación,
                         se crea automáticamente usando DireccionRepository.

        Returns:
            Profesional creado con ID asignado

        Example:
            # Opción 1: Con usuario y dirección existentes
            prof_repo.crear(profesional, usuario_id=uuid_usuario, direccion_id=uuid_dir)

            # Opción 2: Crear todo automáticamente
            profesional.ubicacion = Ubicacion(...)
            prof_repo.crear(profesional)  # Crea usuario y dirección
        """

        if usuario_id is None:
            usuario_orm = UsuarioORM(
                nombre=profesional.nombre,
                apellido=profesional.apellido,
                email=profesional.email,
                celular=profesional.celular,
                es_profesional=True,
                es_solicitante=False,
                activo=profesional.activo,
                verificado=profesional.verificado,
            )
            self.session.add(usuario_orm)
            self.session.flush()
            usuario_id = usuario_orm.id

        if direccion_id is None and profesional.ubicacion:
            direccion_orm = self.direccion_repo.crear_con_jerarquia(
                profesional.ubicacion
            )
            direccion_id = direccion_orm.id

        orm = ProfesionalORM(
            usuario_id=usuario_id,
            direccion_id=direccion_id,
            activo=profesional.activo,
            verificado=profesional.verificado,
        )
        self.session.add(orm)
        self.session.flush()

        if profesional.matriculas:
            from datetime import timedelta

            for mat in profesional.matriculas:
                provincia_orm = (
                    self.session.query(ProvinciaORM)
                    .filter(ProvinciaORM.nombre == mat.provincia)
                    .first()
                )
                if not provincia_orm:
                    raise ValueError(f"Provincia '{mat.provincia}' no encontrada")

                from app.infra.persistence.matriculas import MatriculaORM

                mat_orm = MatriculaORM(
                    profesional_id=orm.id,
                    provincia_id=provincia_orm.id,
                    nro_matricula=mat.numero,
                    vigente_desde=mat.vigente_desde,
                    vigente_hasta=mat.vigente_hasta
                    or (mat.vigente_desde + timedelta(days=3650)),
                )
                self.session.add(mat_orm)

        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def actualizar(
        self, profesional: Profesional, direccion_id: Optional[UUID] = None
    ) -> Profesional:
        """
        Actualiza un profesional existente

        Args:
            profesional: Entidad de dominio con los nuevos datos
            direccion_id: (Opcional) Nueva dirección existente.
                         Si no se proporciona pero profesional.ubicacion cambió,
                         se crea automáticamente.

        Example:
            # Opción 1: Mantener dirección actual
            profesional.email = "nuevo@email.com"
            prof_repo.actualizar(profesional)

            # Opción 2: Cambiar a dirección existente
            prof_repo.actualizar(profesional, direccion_id=nueva_direccion_id)

            # Opción 3: Cambiar ubicación (crea dirección automáticamente)
            profesional.ubicacion = Ubicacion(...)
            prof_repo.actualizar(profesional)  # Crea nueva dirección
        """
        orm = (
            self.session.query(ProfesionalORM)
            .filter(ProfesionalORM.id == profesional.id)
            .first()
        )

        if not orm:
            raise ValueError(f"Profesional con id {profesional.id} no encontrado")

        orm.usuario.nombre = profesional.nombre
        orm.usuario.apellido = profesional.apellido
        orm.usuario.email = profesional.email
        orm.usuario.celular = profesional.celular
        orm.usuario.activo = profesional.activo

        orm.activo = profesional.activo
        orm.verificado = profesional.verificado

        if direccion_id:
            orm.direccion_id = direccion_id
        elif profesional.ubicacion:
            ubicacion_actual = (
                self.direccion_repo._to_domain(orm.direccion) if orm.direccion else None
            )

            if ubicacion_actual != profesional.ubicacion:
                nueva_direccion = self.direccion_repo.crear_con_jerarquia(
                    profesional.ubicacion
                )
                orm.direccion_id = nueva_direccion.id

        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def eliminar(self, id: UUID) -> bool:
        """Elimina físicamente un profesional (NO RECOMENDADO)"""
        orm = (
            self.session.query(ProfesionalORM)
            .filter(ProfesionalORM.id == str(id))
            .first()
        )

        if not orm:
            return False

        self.session.delete(orm)
        self.session.commit()

        return True

    def desactivar(self, id: UUID) -> Optional[Profesional]:
        """Desactivación lógica (RECOMENDADO)"""
        orm = (
            self.session.query(ProfesionalORM)
            .filter(ProfesionalORM.id == str(id))
            .first()
        )

        if not orm:
            return None

        orm.activo = False
        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def buscar_por_especialidad(
        self,
        especialidad_id: Optional[int] = None,
        especialidad_nombre: Optional[str] = None,
    ) -> List[Profesional]:
        """
        Busca profesionales por especialidad (por ID o nombre).
        Prioriza búsqueda por ID si está disponible (más eficiente).
        """
        query = (
            self.session.query(ProfesionalORM)
            .join(ProfesionalORM.especialidades)
            .filter(ProfesionalORM.activo)
        )

        if especialidad_id:
            query = query.filter(EspecialidadORM.id_especialidad == especialidad_id)
        elif especialidad_nombre:
            query = query.filter(
                EspecialidadORM.nombre.ilike(f"%{especialidad_nombre}%")
            )
        else:
            return []

        orms = query.all()
        return [self._to_domain(orm) for orm in orms]

    def buscar_por_ubicacion(
        self,
        provincia: Optional[str] = None,
        departamento: Optional[str] = None,
        barrio: Optional[str] = None,
    ) -> List[Profesional]:
        """
        Busca profesionales por ubicación (provincia, departamento, barrio)

        Usa la jerarquía: Direccion → Barrio → Departamento → Provincia
        """
        query = (
            self.session.query(ProfesionalORM)
            .join(ProfesionalORM.direccion)
            .join(DireccionORM.barrio)
            .join(BarrioORM.departamento)
            .join(DepartamentoORM.provincia)
            .filter(ProfesionalORM.activo)
        )

        if provincia:
            query = query.filter(ProvinciaORM.nombre.ilike(f"%{provincia}%"))
        if departamento:
            query = query.filter(DepartamentoORM.nombre.ilike(f"%{departamento}%"))
        if barrio:
            query = query.filter(BarrioORM.nombre.ilike(f"%{barrio}%"))

        orms = query.all()
        return [self._to_domain(orm) for orm in orms]

    def buscar_combinado(
        self,
        especialidad_id: Optional[int] = None,
        especialidad_nombre: Optional[str] = None,
        provincia: Optional[str] = None,
        departamento: Optional[str] = None,
        barrio: Optional[str] = None,
    ) -> List[Profesional]:
        """
        Busca profesionales por ubicación y/o especialidad.
        Prioriza especialidad_id sobre especialidad_nombre.
        """
        query = self.session.query(ProfesionalORM).filter(ProfesionalORM.activo)

        if provincia or departamento or barrio:
            query = (
                query.join(ProfesionalORM.direccion)
                .join(DireccionORM.barrio)
                .join(BarrioORM.departamento)
                .join(DepartamentoORM.provincia)
            )

            if provincia:
                query = query.filter(ProvinciaORM.nombre.ilike(f"%{provincia}%"))
            if departamento:
                query = query.filter(DepartamentoORM.nombre.ilike(f"%{departamento}%"))
            if barrio:
                query = query.filter(BarrioORM.nombre.ilike(f"%{barrio}%"))

        if especialidad_id or especialidad_nombre:
            query = query.join(ProfesionalORM.especialidades)

            if especialidad_id:
                query = query.filter(EspecialidadORM.id_especialidad == especialidad_id)
            elif especialidad_nombre:
                query = query.filter(
                    EspecialidadORM.nombre.ilike(f"%{especialidad_nombre}%")
                )

        orms = query.all()
        return [self._to_domain(orm) for orm in orms]

    def verificar(self, id: UUID) -> Optional[Profesional]:
        """Marca un profesional como verificado"""
        orm = (
            self.session.query(ProfesionalORM)
            .filter(ProfesionalORM.id == str(id))
            .first()
        )

        if not orm:
            return None

        orm.verificado = True
        self.session.commit()
        self.session.refresh(orm)

        return self._to_domain(orm)

    def contar_profesionales(
        self, solo_activos: bool = False, solo_verificados: bool = False
    ) -> int:
        """Cuenta profesionales con filtros opcionales"""
        query = self.session.query(ProfesionalORM)

        if solo_activos:
            query = query.filter(ProfesionalORM.activo)
        if solo_verificados:
            query = query.filter(ProfesionalORM.verificado)

        return query.count()
