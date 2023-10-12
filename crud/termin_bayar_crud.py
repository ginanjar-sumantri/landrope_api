from crud.base_crud import CRUDBase
from models import TerminBayar
from schemas.termin_bayar_sch import TerminBayarCreateSch, TerminBayarUpdateSch


class CRUDTerminBayar(CRUDBase[TerminBayar, TerminBayarCreateSch, TerminBayarUpdateSch]):
    pass


termin_bayar = CRUDTerminBayar(TerminBayar)
