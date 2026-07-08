"""
Tests para el patrón Observer y Event Bus
Valida Subject, Observer, NotificadorEmail, AuditLogger y EventBus
"""

from uuid import uuid4
from datetime import datetime

from app.domain.observers.observadores import (
    Observer,
    Subject,
    NotificadorEmail,
    AuditLogger,
    EventBus,
)
from app.domain.eventos import (
    Event,
    CitaCreada,
    CitaConfirmada,
    CitaCancelada,
    CitaReprogramada,
    CitaCompletada,
)


class MockObserver(Observer):
    """Observer simulado para tests"""

    def __init__(self):
        self.eventos_recibidos = []
        self.update_count = 0

    def update(self, evt: Event) -> None:
        """Registra evento recibido"""
        self.eventos_recibidos.append(evt)
        self.update_count += 1


class MockSubject(Subject):
    """Subject simulado para tests"""

    def trigger_event(self, evt: Event) -> None:
        """Dispara un evento para notificar observers"""
        self.notify(evt)


class TestSubjectObserverPattern:
    """Tests del patrón Observer GoF"""

    def test_subject_inicializa_sin_observers(self):
        """Subject se inicializa con lista vacía de observers"""
        subject = MockSubject()
        assert len(subject.observers) == 0

    def test_attach_agrega_observer(self):
        """Attach agrega un observer a la lista"""
        subject = MockSubject()
        observer = MockObserver()

        subject.attach(observer)

        assert len(subject.observers) == 1
        assert observer in subject.observers

    def test_attach_no_duplica_observer(self):
        """Attach no agrega el mismo observer dos veces"""
        subject = MockSubject()
        observer = MockObserver()

        subject.attach(observer)
        subject.attach(observer)

        assert len(subject.observers) == 1

    def test_detach_remueve_observer(self):
        """Detach remueve un observer de la lista"""
        subject = MockSubject()
        observer = MockObserver()
        subject.attach(observer)

        subject.detach(observer)

        assert len(subject.observers) == 0
        assert observer not in subject.observers

    def test_detach_observer_no_existente_no_falla(self):
        """Detach de observer no existente no genera error"""
        subject = MockSubject()
        observer = MockObserver()

        subject.detach(observer)
        assert len(subject.observers) == 0

    def test_notify_notifica_a_todos_los_observers(self):
        """Notify llama a update() en todos los observers"""
        subject = MockSubject()
        obs1 = MockObserver()
        obs2 = MockObserver()
        obs3 = MockObserver()

        subject.attach(obs1)
        subject.attach(obs2)
        subject.attach(obs3)

        evento = Event(tipo="test.evento", cita_id=uuid4(), datos={"test": "data"})
        subject.notify(evento)

        assert obs1.update_count == 1
        assert obs2.update_count == 1
        assert obs3.update_count == 1
        assert obs1.eventos_recibidos[0] == evento
        assert obs2.eventos_recibidos[0] == evento
        assert obs3.eventos_recibidos[0] == evento

    def test_multiple_notificaciones(self):
        """Subject puede notificar múltiples veces"""
        subject = MockSubject()
        observer = MockObserver()
        subject.attach(observer)

        evento1 = Event(tipo="test.1", cita_id=uuid4(), datos={})
        evento2 = Event(tipo="test.2", cita_id=uuid4(), datos={})
        evento3 = Event(tipo="test.3", cita_id=uuid4(), datos={})

        subject.notify(evento1)
        subject.notify(evento2)
        subject.notify(evento3)

        assert observer.update_count == 3
        assert len(observer.eventos_recibidos) == 3

    def test_notify_sin_observers_no_falla(self):
        """Notify sin observers no genera error"""
        subject = MockSubject()
        evento = Event(tipo="test", cita_id=uuid4(), datos={})

        subject.notify(evento)


class TestNotificadorEmail:
    """Tests para NotificadorEmail observer"""

    def setup_method(self):
        """Setup antes de cada test"""
        self.notificador = NotificadorEmail()
        self.cita_id = uuid4()
        self.prof_id = uuid4()
        self.pac_id = uuid4()

    def test_notificador_es_observer(self):
        """NotificadorEmail es una instancia de Observer"""
        assert isinstance(self.notificador, Observer)

    def test_procesa_cita_creada(self, capsys):
        """Procesa evento CitaCreada correctamente"""
        evento = CitaCreada(
            cita_id=self.cita_id,
            profesional_id=self.prof_id,
            paciente_id=self.pac_id,
        )

        self.notificador.update(evento)

        captured = capsys.readouterr()
        assert "CITA CREADA" in captured.out
        assert str(self.cita_id) in captured.out
        assert str(self.prof_id) in captured.out
        assert str(self.pac_id) in captured.out

    def test_procesa_cita_confirmada(self, capsys):
        """Procesa evento CitaConfirmada correctamente"""
        evento = CitaConfirmada(cita_id=self.cita_id, confirmado_por="Profesional")

        self.notificador.update(evento)

        captured = capsys.readouterr()
        assert "CITA CONFIRMADA" in captured.out
        assert str(self.cita_id) in captured.out
        assert "Profesional" in captured.out

    def test_procesa_cita_cancelada(self, capsys):
        """Procesa evento CitaCancelada correctamente"""
        evento = CitaCancelada(
            cita_id=self.cita_id,
            motivo="Paciente enfermo",
            cancelado_por="Solicitante",
        )

        self.notificador.update(evento)

        captured = capsys.readouterr()
        assert "CITA CANCELADA" in captured.out
        assert str(self.cita_id) in captured.out
        assert "Paciente enfermo" in captured.out
        assert "Solicitante" in captured.out

    def test_procesa_cita_reprogramada(self, capsys):
        """Procesa evento CitaReprogramada correctamente"""
        evento = CitaReprogramada(
            cita_id=self.cita_id,
            fecha_anterior="2025-11-15 10:00",
            fecha_nueva="2025-11-20 14:00",
        )

        self.notificador.update(evento)

        captured = capsys.readouterr()
        assert "CITA REPROGRAMADA" in captured.out
        assert str(self.cita_id) in captured.out
        assert "2025-11-15 10:00" in captured.out
        assert "2025-11-20 14:00" in captured.out

    def test_procesa_cita_completada(self, capsys):
        """Procesa evento CitaCompletada correctamente"""
        evento = CitaCompletada(cita_id=self.cita_id, notas="Consulta exitosa")

        self.notificador.update(evento)

        captured = capsys.readouterr()
        assert "CITA COMPLETADA" in captured.out
        assert str(self.cita_id) in captured.out
        assert "Consulta exitosa" in captured.out

    def test_procesa_evento_desconocido_no_falla(self):
        """Eventos desconocidos no generan error"""
        evento = Event(tipo="tipo.desconocido", cita_id=self.cita_id, datos={})

        self.notificador.update(evento)


class TestAuditLogger:
    """Tests para AuditLogger observer"""

    def test_audit_logger_es_observer(self):
        """AuditLogger es una instancia de Observer"""
        logger = AuditLogger()
        assert isinstance(logger, Observer)

    def test_registra_evento_en_log(self, caplog):
        """AuditLogger registra eventos en log"""
        logger = AuditLogger()
        cita_id = uuid4()
        evento = CitaCreada(
            cita_id=cita_id, profesional_id=uuid4(), paciente_id=uuid4()
        )

        with caplog.at_level("INFO"):
            logger.update(evento)

        assert any("[AUDIT]" in record.message for record in caplog.records)
        assert any("cita.creada" in record.message for record in caplog.records)
        assert any(str(cita_id) in record.message for record in caplog.records)


class TestEventBus:
    """Tests para EventBus (pub/sub pattern)"""

    def setup_method(self):
        """Setup antes de cada test"""
        self.bus = EventBus()

    def test_event_bus_inicializa_sin_suscriptores(self):
        """EventBus se inicializa sin suscriptores"""
        assert len(self.bus._suscriptores) == 0

    def test_suscribir_handler_a_evento(self):
        """Puede suscribir un handler a un tipo de evento"""
        eventos_procesados = []

        def handler(evt):
            eventos_procesados.append(evt)

        self.bus.suscribir("cita.creada", handler)

        assert "cita.creada" in self.bus._suscriptores
        assert len(self.bus._suscriptores["cita.creada"]) == 1

    def test_publicar_evento_ejecuta_handler(self):
        """Publicar evento ejecuta handler suscrito"""
        eventos_procesados = []

        def handler(evt):
            eventos_procesados.append(evt)

        self.bus.suscribir("cita.creada", handler)

        evento = CitaCreada(
            cita_id=uuid4(), profesional_id=uuid4(), paciente_id=uuid4()
        )
        self.bus.publicar(evento)

        assert len(eventos_procesados) == 1
        assert eventos_procesados[0] == evento

    def test_multiples_handlers_mismo_evento(self):
        """Múltiples handlers pueden suscribirse al mismo evento"""
        count = {"handler1": 0, "handler2": 0, "handler3": 0}

        def handler1(evt):
            count["handler1"] += 1

        def handler2(evt):
            count["handler2"] += 1

        def handler3(evt):
            count["handler3"] += 1

        self.bus.suscribir("cita.creada", handler1)
        self.bus.suscribir("cita.creada", handler2)
        self.bus.suscribir("cita.creada", handler3)

        evento = CitaCreada(
            cita_id=uuid4(), profesional_id=uuid4(), paciente_id=uuid4()
        )
        self.bus.publicar(evento)

        assert count["handler1"] == 1
        assert count["handler2"] == 1
        assert count["handler3"] == 1

    def test_publicar_sin_suscriptores_no_falla(self):
        """Publicar evento sin suscriptores no genera error"""
        evento = Event(tipo="evento.sin.suscriptores", cita_id=uuid4(), datos={})

        self.bus.publicar(evento)

    def test_suscribir_observer_tradicional(self):
        """Puede suscribir Observer tradicional a EventBus"""
        observer = MockObserver()
        self.bus.suscribir_observer("cita.creada", observer)

        evento = CitaCreada(
            cita_id=uuid4(), profesional_id=uuid4(), paciente_id=uuid4()
        )
        self.bus.publicar(evento)

        assert observer.update_count == 1
        assert len(observer.eventos_recibidos) == 1

    def test_error_en_handler_no_detiene_otros_handlers(self, caplog):
        """Error en un handler no detiene ejecución de otros"""
        eventos_procesados = []

        def handler_ok(evt):
            eventos_procesados.append(evt)

        def handler_falla(evt):
            raise RuntimeError("Error simulado")

        def handler_ok2(evt):
            eventos_procesados.append(evt)

        self.bus.suscribir("cita.creada", handler_ok)
        self.bus.suscribir("cita.creada", handler_falla)
        self.bus.suscribir("cita.creada", handler_ok2)

        evento = CitaCreada(
            cita_id=uuid4(), profesional_id=uuid4(), paciente_id=uuid4()
        )

        with caplog.at_level("ERROR"):
            self.bus.publicar(evento)

        assert len(eventos_procesados) == 2
        assert any(
            "Error procesando evento" in record.message for record in caplog.records
        )


class TestIntegracionObserverEventBus:
    """Tests de integración entre Observer pattern y EventBus"""

    def test_flujo_completo_notificaciones(self, capsys):
        """Flujo completo: Evento → EventBus → Observers"""
        bus = EventBus()
        notificador = NotificadorEmail()
        audit = AuditLogger()

        bus.suscribir_observer("cita.creada", notificador)
        bus.suscribir_observer("cita.creada", audit)
        bus.suscribir_observer("cita.cancelada", notificador)

        cita_id = uuid4()
        evento_creada = CitaCreada(
            cita_id=cita_id, profesional_id=uuid4(), paciente_id=uuid4()
        )
        bus.publicar(evento_creada)
        captured = capsys.readouterr()
        assert "CITA CREADA" in captured.out

        evento_cancelada = CitaCancelada(cita_id=cita_id, motivo="Test cancelación")
        bus.publicar(evento_cancelada)

        captured = capsys.readouterr()
        assert "CITA CANCELADA" in captured.out

    def test_subject_con_notificador_email(self, capsys):
        """Subject + NotificadorEmail + CitaCreada"""
        subject = MockSubject()
        notificador = NotificadorEmail()
        subject.attach(notificador)

        evento = CitaCreada(
            cita_id=uuid4(), profesional_id=uuid4(), paciente_id=uuid4()
        )
        subject.trigger_event(evento)

        captured = capsys.readouterr()
        assert "NOTIFICADOR EMAIL" in captured.out
        assert "CITA CREADA" in captured.out

    def test_combinar_subject_y_eventbus(self):
        """Puede combinar Subject y EventBus en el mismo flujo"""
        subject = MockSubject()
        obs1 = MockObserver()
        subject.attach(obs1)

        bus = EventBus()
        obs2 = MockObserver()
        bus.suscribir_observer("cita.creada", obs2)

        evento = CitaCreada(
            cita_id=uuid4(), profesional_id=uuid4(), paciente_id=uuid4()
        )

        subject.notify(evento)
        bus.publicar(evento)

        assert obs1.update_count == 1
        assert obs2.update_count == 1


class TestEventosDominio:
    """Tests para clases de eventos del dominio"""

    def test_evento_base_inicializa_con_timestamp(self):
        """Event base agrega timestamp automáticamente"""
        evento = Event(tipo="test", cita_id=uuid4(), datos={})
        assert evento.timestamp is not None
        assert isinstance(evento.timestamp, datetime)

    def test_cita_creada_tiene_tipo_correcto(self):
        """CitaCreada tiene tipo 'cita.creada'"""
        evento = CitaCreada(
            cita_id=uuid4(), profesional_id=uuid4(), paciente_id=uuid4()
        )
        assert evento.tipo == "cita.creada"

    def test_cita_confirmada_tiene_tipo_correcto(self):
        """CitaConfirmada tiene tipo 'cita.confirmada'"""
        evento = CitaConfirmada(cita_id=uuid4())
        assert evento.tipo == "cita.confirmada"

    def test_cita_cancelada_tiene_tipo_correcto(self):
        """CitaCancelada tiene tipo 'cita.cancelada'"""
        evento = CitaCancelada(cita_id=uuid4())
        assert evento.tipo == "cita.cancelada"

    def test_cita_reprogramada_tiene_tipo_correcto(self):
        """CitaReprogramada tiene tipo 'cita.reprogramada'"""
        evento = CitaReprogramada(
            cita_id=uuid4(), fecha_anterior="old", fecha_nueva="new"
        )
        assert evento.tipo == "cita.reprogramada"

    def test_cita_completada_tiene_tipo_correcto(self):
        """CitaCompletada tiene tipo 'cita.completada'"""
        evento = CitaCompletada(cita_id=uuid4())
        assert evento.tipo == "cita.completada"

    def test_eventos_contienen_datos_correctos(self):
        """Eventos almacenan datos en dict"""
        cita_id = uuid4()
        prof_id = uuid4()
        pac_id = uuid4()

        evento = CitaCreada(cita_id=cita_id, profesional_id=prof_id, paciente_id=pac_id)

        assert evento.cita_id == cita_id
        assert evento.datos["profesional_id"] == str(prof_id)
        assert evento.datos["paciente_id"] == str(pac_id)
