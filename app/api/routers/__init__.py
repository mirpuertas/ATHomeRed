"""
Exporta todos los routers para facilitar la importación
"""

from . import auth
from . import profesionales
from . import consultas
from . import pacientes
from . import busqueda

__all__ = ["auth", "profesionales", "consultas", "pacientes", "busqueda"]
