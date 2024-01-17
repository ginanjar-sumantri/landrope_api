from crud.base_crud import CRUDBase
from models.kjb_model import KjbHistory
from schemas.kjb_history_sch import KjbHistoryCreateSch

class CRUDKjbHistory(CRUDBase[KjbHistory, KjbHistoryCreateSch, KjbHistoryCreateSch]):
    pass

kjb_history = CRUDKjbHistory(KjbHistory)