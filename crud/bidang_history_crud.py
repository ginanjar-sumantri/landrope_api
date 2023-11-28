from crud.base_crud import CRUDBase
from models.bidang_model import BidangHistory
from schemas.bidang_history_sch import BidangHistoryCreateSch

class CRUDBidangHistory(CRUDBase[BidangHistory, BidangHistoryCreateSch, BidangHistoryCreateSch]):
    pass

bidang_history = CRUDBidangHistory(BidangHistory)