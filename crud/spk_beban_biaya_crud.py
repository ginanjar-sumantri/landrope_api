from crud.base_crud import CRUDBase
from models.spk_model import SpkBebanBiaya
from schemas.spk_beban_biaya_sch import SpkBebanBiayaCreateSch, SpkBebanBiayaUpdateSch

class CRUDSpkBebanBiaya(CRUDBase[SpkBebanBiaya, SpkBebanBiayaCreateSch, SpkBebanBiayaUpdateSch]):
    pass

spk_beban_biaya = CRUDSpkBebanBiaya(SpkBebanBiaya)