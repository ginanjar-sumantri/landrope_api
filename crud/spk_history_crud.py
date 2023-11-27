from crud.base_crud import CRUDBase
from models.spk_model import SpkHistory
from schemas.spk_history_sch import SpkHistoryCreateSch

class CRUDSpkHistory(CRUDBase[SpkHistory, SpkHistoryCreateSch, SpkHistoryCreateSch]):
    pass

spk_history = CRUDSpkHistory(SpkHistory)