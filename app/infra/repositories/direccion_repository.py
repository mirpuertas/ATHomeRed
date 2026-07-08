from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from uuid import UUID

from app.domain.value_objects.objetos_valor import Ubicacion
from app.infra.persistence.ubicacion import (
    ProvinciaORM,
    DepartamentoORM,
    BarrioORM,
    DireccionORM,
)


class DireccionRepository:
    """
    Repositorio para gestionar la jerarquía de ubicaciones:
    Provincia → Departamento → Barrio → Dirección

    Permite:
    - Crear direcciones completas con toda la jerarquía
    - Buscar o crear elementos de la jerarquía (evita duplicados)
    - Consultar catálogos (provincias, departamentos, barrios)
    - Convertir entre Ubicacion (value object) y DireccionORM
    """

    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, orm: DireccionORM) -> Ubicacion:
        """Convierte DireccionORM a Ubicacion (value object)"""
        return Ubicacion(
            provincia=orm.barrio.departamento.provincia.nombre,
            departamento=orm.barrio.departamento.nombre,
            barrio=orm.barrio.nombre,
            calle=orm.calle,
            numero=str(orm.numero),
        )

    def buscar_o_crear_provincia(self, nombre: str) -> ProvinciaORM:
        """
        Busca una provincia por nombre (case-insensitive).
        Si no existe, la crea.
        """
        nombre = nombre.strip().title()

        provincia = (
            self.session.query(ProvinciaORM)
            .filter(ProvinciaORM.nombre.ilike(nombre))
            .first()
        )

        if provincia:
            return provincia

        provincia = ProvinciaORM(nombre=nombre)
        self.session.add(provincia)
        self.session.flush()

        return provincia

    def buscar_o_crear_departamento(
        self, nombre: str, provincia: ProvinciaORM
    ) -> DepartamentoORM:
        """
        Busca un departamento por nombre y provincia.
        Si no existe, lo crea.
        """

        nombre = nombre.strip().title()

        departamento = (
            self.session.query(DepartamentoORM)
            .filter(
                DepartamentoORM.nombre.ilike(nombre),
                DepartamentoORM.provincia_id == provincia.id,
            )
            .first()
        )

        if departamento:
            return departamento

        departamento = DepartamentoORM(nombre=nombre, provincia_id=provincia.id)
        self.session.add(departamento)
        self.session.flush()

        return departamento

    def buscar_o_crear_barrio(
        self, nombre: str, departamento: DepartamentoORM
    ) -> BarrioORM:
        """
        Busca un barrio por nombre y departamento.
        Si no existe, lo crea.
        """

        nombre = nombre.strip().title()

        barrio = (
            self.session.query(BarrioORM)
            .filter(
                BarrioORM.nombre.ilike(nombre),
                BarrioORM.departamento_id == departamento.id,
            )
            .first()
        )

        if barrio:
            return barrio

        barrio = BarrioORM(nombre=nombre, departamento_id=departamento.id)
        self.session.add(barrio)
        self.session.flush()

        return barrio

    def crear_con_jerarquia(self, ubicacion: Ubicacion) -> DireccionORM:
        """
        Crea una dirección completa con toda la jerarquía.

        Busca o crea automáticamente:
        - Provincia
        - Departamento
        - Barrio
        - Dirección

        Args:
            ubicacion: Value object con los datos de ubicación

        Returns:
            DireccionORM creada (con ID asignado)

        Example:
            ubicacion = Ubicacion(
                provincia="Buenos Aires",
                departamento="Capital Federal",
                barrio="Palermo",
                calle="Av. Santa Fe",
                numero="3500"
            )
            direccion = repo.crear_con_jerarquia(ubicacion)
        """

        provincia = self.buscar_o_crear_provincia(ubicacion.provincia)

        departamento = self.buscar_o_crear_departamento(
            ubicacion.departamento, provincia
        )

        barrio = self.buscar_o_crear_barrio(ubicacion.barrio, departamento)

        direccion = (
            self.session.query(DireccionORM)
            .filter(
                DireccionORM.barrio_id == barrio.id,
                DireccionORM.calle.ilike(ubicacion.calle),
                DireccionORM.numero == int(ubicacion.numero),
            )
            .first()
        )

        if direccion:
            return direccion

        direccion = DireccionORM(
            barrio_id=barrio.id,
            calle=ubicacion.calle.strip(),
            numero=int(ubicacion.numero),
        )
        self.session.add(direccion)
        self.session.flush()

        return direccion

    def obtener_por_id(self, id: UUID) -> Optional[DireccionORM]:
        """Obtiene una dirección por su ID"""
        return self.session.query(DireccionORM).filter(DireccionORM.id == id).first()

    def buscar_direccion(
        self,
        provincia: str,
        departamento: str,
        barrio: str,
        calle: str,
        numero: str,
    ) -> Optional[DireccionORM]:
        """
        Busca una dirección exacta por todos sus componentes.

        Útil para evitar duplicados antes de crear.
        """
        return (
            self.session.query(DireccionORM)
            .join(DireccionORM.barrio)
            .join(BarrioORM.departamento)
            .join(DepartamentoORM.provincia)
            .filter(
                ProvinciaORM.nombre.ilike(provincia),
                DepartamentoORM.nombre.ilike(departamento),
                BarrioORM.nombre.ilike(barrio),
                DireccionORM.calle.ilike(calle),
                DireccionORM.numero == int(numero),
            )
            .first()
        )

    def listar_provincias(self) -> List[ProvinciaORM]:
        """Lista todas las provincias disponibles"""
        return self.session.query(ProvinciaORM).order_by(ProvinciaORM.nombre).all()

    def listar_departamentos(self, provincia_id: UUID) -> List[DepartamentoORM]:
        """Lista todos los departamentos de una provincia"""
        return (
            self.session.query(DepartamentoORM)
            .filter(DepartamentoORM.provincia_id == provincia_id)
            .order_by(DepartamentoORM.nombre)
            .all()
        )

    def listar_barrios(self, departamento_id: UUID) -> List[BarrioORM]:
        """Lista todos los barrios de un departamento"""
        return (
            self.session.query(BarrioORM)
            .filter(BarrioORM.departamento_id == departamento_id)
            .order_by(BarrioORM.nombre)
            .all()
        )

    def listar_direcciones_por_barrio(self, barrio_id: UUID) -> List[DireccionORM]:
        """Lista todas las direcciones de un barrio"""
        return (
            self.session.query(DireccionORM)
            .filter(DireccionORM.barrio_id == barrio_id)
            .order_by(DireccionORM.calle, DireccionORM.numero)
            .all()
        )

    def buscar_direcciones(
        self,
        provincia: Optional[str] = None,
        departamento: Optional[str] = None,
        barrio: Optional[str] = None,
        calle: Optional[str] = None,
    ) -> List[DireccionORM]:
        """
        Busca direcciones con filtros opcionales.

        Todos los parámetros son opcionales y combinables.
        La búsqueda es case-insensitive y permite coincidencias parciales.
        """
        query = (
            self.session.query(DireccionORM)
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
        if calle:
            query = query.filter(DireccionORM.calle.ilike(f"%{calle}%"))

        return query.order_by(
            ProvinciaORM.nombre,
            DepartamentoORM.nombre,
            BarrioORM.nombre,
            DireccionORM.calle,
            DireccionORM.numero,
        ).all()

    def obtener_jerarquia_completa(
        self, direccion_id: UUID
    ) -> Optional[Tuple[ProvinciaORM, DepartamentoORM, BarrioORM, DireccionORM]]:
        """
        Obtiene la jerarquía completa de una dirección.

        Returns:
            Tuple con (Provincia, Departamento, Barrio, Dirección) o None
        """
        direccion = (
            self.session.query(DireccionORM)
            .filter(DireccionORM.id == direccion_id)
            .first()
        )

        if not direccion:
            return None

        barrio = direccion.barrio
        departamento = barrio.departamento
        provincia = departamento.provincia

        return (provincia, departamento, barrio, direccion)

    def actualizar_coordenadas(
        self, direccion_id: UUID, latitud: float, longitud: float
    ) -> Optional[DireccionORM]:
        """
        Actualiza las coordenadas GPS de una dirección.

        Útil para integrar con servicios de geocoding.
        """
        direccion = self.obtener_por_id(direccion_id)

        if not direccion:
            return None

        if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
            raise ValueError("Coordenadas fuera de rango válido")

        direccion.latitud = latitud
        direccion.longitud = longitud

        self.session.flush()

        return direccion

    def contar_provincias(self) -> int:
        """Cuenta el total de provincias"""
        return self.session.query(ProvinciaORM).count()

    def contar_departamentos(self, provincia_id: Optional[UUID] = None) -> int:
        """Cuenta departamentos (opcionalmente filtrados por provincia)"""
        query = self.session.query(DepartamentoORM)

        if provincia_id:
            query = query.filter(DepartamentoORM.provincia_id == provincia_id)

        return query.count()

    def contar_barrios(self, departamento_id: Optional[UUID] = None) -> int:
        """Cuenta barrios (opcionalmente filtrados por departamento)"""
        query = self.session.query(BarrioORM)

        if departamento_id:
            query = query.filter(BarrioORM.departamento_id == departamento_id)

        return query.count()

    def contar_direcciones(self, barrio_id: Optional[UUID] = None) -> int:
        """Cuenta direcciones (opcionalmente filtradas por barrio)"""
        query = self.session.query(DireccionORM)

        if barrio_id:
            query = query.filter(DireccionORM.barrio_id == barrio_id)

        return query.count()
