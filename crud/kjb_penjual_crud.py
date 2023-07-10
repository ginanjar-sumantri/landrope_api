from crud.base_crud import CRUDBase
from models.kjb_model import KjbPenjual
from schemas.kjb_penjual_sch import KjbPenjualCreateSch, KjbPenjualUpdateSch


class CRUDKjbPenjual(CRUDBase[KjbPenjual, KjbPenjualCreateSch, KjbPenjualUpdateSch]):
    pass

kjb_penjual = CRUDKjbPenjual(KjbPenjual)