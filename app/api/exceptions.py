"""
Excepciones personalizadas para la API
"""


class BusinessRuleException(Exception):
    """
    Excepción base para violaciones de reglas de negocio.
    Se mapea a HTTP 400 Bad Request.
    """

    pass


class ResourceNotFoundException(Exception):
    """
    Excepción cuando un recurso no existe.
    Se mapea a HTTP 404 Not Found.
    """

    pass


class UnauthorizedException(Exception):
    """
    Excepción para accesos no autorizados.
    Se mapea a HTTP 401 Unauthorized.
    """

    pass


class ForbiddenException(Exception):
    """
    Excepción para accesos prohibidos (sin permisos).
    Se mapea a HTTP 403 Forbidden.
    """

    pass


class ConflictException(Exception):
    """
    Excepción para conflictos (ej: datos duplicados).
    Se mapea a HTTP 409 Conflict.
    """

    pass
