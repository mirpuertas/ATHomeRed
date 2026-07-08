"""
Tests unitarios para las entities del domain
"""

from datetime import date
from uuid import uuid4

from app.domain.entities.usuarios import (
    Usuario,
    Profesional,
    Solicitante,
    Paciente,
)
from app.domain.value_objects.objetos_valor import (
    Ubicacion,
)


class TestUbicacion:
    """Tests para Ubicacion (Value Object)"""

    def test_crear_ubicacion(self, ubicacion_buenos_aires):
        """Crear una ubicación correctamente"""
        assert ubicacion_buenos_aires.provincia == "Buenos Aires"
        assert ubicacion_buenos_aires.departamento == "CABA"
        assert ubicacion_buenos_aires.barrio == "Flores"
        assert ubicacion_buenos_aires.latitud == -34.6037

    def test_ubicaciones_iguales_son_equivalentes(self):
        """Dos ubicaciones con los mismos datos son equivalentes"""
        ub1 = Ubicacion(
            provincia="Buenos Aires",
            departamento="CABA",
            barrio="Flores",
            calle="Av. Acoyte",
            numero=1234,
            latitud=-34.6037,
            longitud=-58.3816,
        )
        ub2 = Ubicacion(
            provincia="Buenos Aires",
            departamento="CABA",
            barrio="Flores",
            calle="Av. Acoyte",
            numero=1234,
            latitud=-34.6037,
            longitud=-58.3816,
        )

        assert ub1 == ub2


class TestEspecialidad:
    """Tests para Especialidad"""

    def test_crear_especialidad(self, especialidad_enfermeria):
        """Crear una especialidad"""
        assert especialidad_enfermeria.id == 1
        assert especialidad_enfermeria.nombre == "Enfermería"

    def test_especialidades_diferentes(
        self, especialidad_enfermeria, especialidad_acompanante
    ):
        """Especialidades diferentes tienen IDs distintos"""
        assert especialidad_enfermeria.id != especialidad_acompanante.id
        assert especialidad_enfermeria.nombre != especialidad_acompanante.nombre


class TestUsuario:
    """Tests para Usuario (clase abstracta)"""

    def test_nombre_completo(self, profesional_enfermeria):
        """La propiedad nombre_completo funciona"""
        assert profesional_enfermeria.nombre_completo == "Ana López"

    def test_activar_usuario(self, profesional_enfermeria):
        """Activar un usuario desactivado"""
        profesional_enfermeria.activo = False
        profesional_enfermeria.activar()
        assert profesional_enfermeria.activo is True

    def test_desactivar_usuario(self, profesional_enfermeria):
        """Desactivar un usuario activo"""
        profesional_enfermeria.activo = True
        profesional_enfermeria.desactivar()
        assert profesional_enfermeria.activo is False

    def test_datos_contacto(self, profesional_enfermeria):
        """El método datos_contacto retorna info formateada"""
        contacto = profesional_enfermeria.datos_contacto()
        assert "Ana López" in contacto
        assert "ana.lopez@athomered.com" in contacto
        assert "1123456789" in contacto


class TestProfesional:
    """Tests para Profesional"""

    def test_crear_profesional(self, profesional_enfermeria):
        """Crear un profesional correctamente"""
        assert profesional_enfermeria.nombre == "Ana"
        assert profesional_enfermeria.apellido == "López"
        assert profesional_enfermeria.verificado is True
        assert len(profesional_enfermeria.especialidades) > 0

    def test_profesional_no_verificado_por_defecto(
        self, ubicacion_buenos_aires, especialidad_enfermeria
    ):
        """Un profesional nuevo no está verificado por defecto"""
        prof = Profesional(
            id=uuid4(),
            nombre="Test",
            apellido="Prof",
            email="test@example.com",
            celular="123456789",
            ubicacion=ubicacion_buenos_aires,
            especialidades=[especialidad_enfermeria],
        )

        assert prof.verificado is False

    def test_agregar_disponibilidad(
        self, profesional_enfermeria, disponibilidad_miercoles_tarde
    ):
        """Agregar disponibilidad a un profesional"""
        cantidad_inicial = len(profesional_enfermeria.disponibilidades)

        profesional_enfermeria.agregar_disponibilidad(disponibilidad_miercoles_tarde)

        assert len(profesional_enfermeria.disponibilidades) == cantidad_inicial + 1
        assert disponibilidad_miercoles_tarde in profesional_enfermeria.disponibilidades

    def test_profesional_hereda_de_usuario(self, profesional_enfermeria):
        """Profesional tiene métodos de Usuario"""
        profesional_enfermeria.desactivar()
        assert profesional_enfermeria.activo is False

        profesional_enfermeria.activar()
        assert profesional_enfermeria.activo is True

    def test_profesional_con_multiples_especialidades(
        self,
        ubicacion_buenos_aires,
        especialidad_enfermeria,
        especialidad_acompanante,
    ):
        """Un profesional puede tener múltiples especialidades"""
        prof = Profesional(
            id=uuid4(),
            nombre="Multi",
            apellido="Especialista",
            email="multi@example.com",
            celular="123456789",
            ubicacion=ubicacion_buenos_aires,
            especialidades=[
                especialidad_enfermeria,
                especialidad_acompanante,
            ],
        )

        assert len(prof.especialidades) == 2
        assert especialidad_enfermeria in prof.especialidades
        assert especialidad_acompanante in prof.especialidades


class TestSolicitante:
    """Tests para Solicitante"""

    def test_crear_solicitante(self, solicitante):
        """Crear un solicitante"""
        assert solicitante.nombre == "Carlos"
        assert solicitante.apellido == "López"
        assert solicitante.pacientes == []

    def test_solicitante_activo_por_defecto(self, ubicacion_buenos_aires):
        """Un solicitante es activo por defecto"""
        sol = Solicitante(
            id=uuid4(),
            nombre="Test",
            apellido="Solicitante",
            email="test@example.com",
            celular="123456789",
            ubicacion=ubicacion_buenos_aires,
        )

        assert sol.activo is True

    def test_agregar_paciente(self, solicitante, paciente):
        """Agregar un paciente al solicitante"""
        assert paciente in solicitante.pacientes

    def test_agregar_mismo_paciente_dos_veces(self, solicitante, paciente):
        """No se puede agregar el mismo paciente dos veces"""
        cantidad_inicial = len(solicitante.pacientes)

        solicitante.agregar_paciente(paciente)

        assert len(solicitante.pacientes) == cantidad_inicial

    def test_solicitante_pacientes_lista_vacia_al_inicio(self, solicitante):
        """Un solicitante comienza sin pacientes"""
        assert isinstance(solicitante.pacientes, list)
        assert len(solicitante.pacientes) == 0

    def test_solicitante_hereda_de_usuario(self, solicitante):
        """Solicitante tiene métodos de Usuario"""
        solicitante.desactivar()
        assert solicitante.activo is False

        assert "Carlos López" == solicitante.nombre_completo


class TestPaciente:
    """Tests para Paciente (NO hereda de Usuario)"""

    def test_crear_paciente(self, paciente):
        """Crear un paciente"""
        assert paciente.nombre == "Roberto"
        assert paciente.apellido == "Fernández"
        assert paciente.fecha_nacimiento == date(1979, 5, 15)
        assert paciente.relacion == "self"

    def test_edad_paciente(self, paciente):
        """Calcular edad del paciente"""
        edad = paciente.edad()
        assert edad == 46

    def test_edad_paciente_en_fecha_especifica(self, paciente):
        """Calcular edad en una fecha específica"""
        fecha_test = date(2025, 5, 10)
        edad = paciente.edad(fecha_test)
        assert edad == 45

        fecha_test2 = date(2025, 5, 20)
        edad2 = paciente.edad(fecha_test2)
        assert edad2 == 46

    def test_edad_paciente_en_dia_cumpleaños(self, paciente):
        """Calcular edad el día del cumpleaños"""
        fecha_test = date(2025, 5, 15)
        edad = paciente.edad(fecha_test)
        assert edad == 46

    def test_paciente_hijo(self, paciente_hijo):
        """Paciente con relación 'hijo'"""
        assert paciente_hijo.relacion == "hijo"
        assert paciente_hijo.nombre == "Lucas"

    def test_paciente_con_notas(self, solicitante):
        """Paciente puede tener notas"""
        paciente = Paciente(
            id=uuid4(),
            nombre="Test",
            apellido="Paciente",
            fecha_nacimiento=date(2000, 1, 1),
            ubicacion=solicitante.ubicacion,
            solicitante_id=solicitante.id,
            notas="Alergias a penicilina",
        )

        assert paciente.notas == "Alergias a penicilina"

    def test_nombre_completo_paciente(self, paciente):
        """Paciente tiene nombre completo como propiedad"""
        assert paciente.nombre_completo == "Roberto Fernández"

    def test_paciente_no_es_usuario(self, paciente):
        """Paciente NO hereda de Usuario"""
        assert not isinstance(paciente, Usuario)
        assert not hasattr(paciente, "activar")


class TestIntegracionEntities:
    """Tests de integración entre entities"""

    def test_flujo_creacion_solicitante_con_pacientes(
        self, solicitante, paciente, paciente_hijo
    ):
        """Flujo completo: crear solicitante con pacientes"""
        assert solicitante.nombre_completo == "Carlos López"
        assert len(solicitante.pacientes) == 2

        assert paciente.solicitante_id == solicitante.id
        assert paciente_hijo.solicitante_id == solicitante.id

    def test_flujo_profesional_con_especialidades(
        self, profesional_enfermeria, disponibilidad_miercoles_tarde
    ):
        """Flujo completo: profesional con especialidades y disponibilidades"""
        profesional_enfermeria.agregar_disponibilidad(disponibilidad_miercoles_tarde)

        assert len(profesional_enfermeria.especialidades) >= 1
        assert len(profesional_enfermeria.disponibilidades) == 2
        assert len(profesional_enfermeria.matriculas) >= 1

    def test_diferencia_usuario_vs_paciente(self, profesional_enfermeria, paciente):
        """Los profesionales son usuarios, los pacientes no"""
        assert isinstance(profesional_enfermeria, Usuario)
        assert not isinstance(paciente, Usuario)

        assert hasattr(profesional_enfermeria, "activar")
        assert not hasattr(paciente, "activar")
