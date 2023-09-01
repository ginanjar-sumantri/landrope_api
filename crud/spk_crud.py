from crud.base_crud import CRUDBase
from models.spk_model import Spk
from schemas.spk_sch import SpkCreateSch, SpkUpdateSch

class CRUDSpk(CRUDBase[Spk, SpkCreateSch, SpkUpdateSch]):
    pass

spk = CRUDSpk(Spk)