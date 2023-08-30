from crud.base_crud import CRUDBase
from models.giro_model import Giro
from schemas.giro_sch import GiroCreateSch, GiroUpdateSch

class CRUDGiro(CRUDBase[Giro, GiroCreateSch, GiroUpdateSch]):
    pass

giro = CRUDGiro(Giro)