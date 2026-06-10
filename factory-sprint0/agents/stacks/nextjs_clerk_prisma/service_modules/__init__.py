"""
service_modules/__init__.py
────────────────────────────
Registre ordonné des ServiceMethodModules.

L'ordre détermine l'ordre des méthodes dans le fichier .service.ts généré.
Ajouter un module = l'instancier ici et l'insérer dans SERVICE_MODULES.
"""
from .crud import CrudModule
from .child import ChildModule
from .status import StatusModule
from .public import PublicModule
from .relations import RelationsModule
from .public_relations import PublicRelationsModule
from .slug import SlugModule

SERVICE_MODULES = [
    CrudModule(),
    ChildModule(),
    StatusModule(),
    PublicModule(),
    RelationsModule(),
    PublicRelationsModule(),
    SlugModule(),
]

__all__ = ["SERVICE_MODULES"]
