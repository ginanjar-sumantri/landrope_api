from crud.base_crud import CRUDBase
from models.notaris_model import Notaris
from schemas.notaris_sch import NotarisCreateSch, NotarisUpdateSch


class CRUDNotaris(CRUDBase[Notaris, NotarisCreateSch, NotarisUpdateSch]):
    pass

notaris = CRUDNotaris(Notaris)