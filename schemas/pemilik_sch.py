from models.pemilik_model import PemilikBase, PemilikFullBase, Kontak, Rekening
from common.partial import optional
from typing import List
from schemas.kontak_sch import KontakCreateExtSch
from schemas.rekening_sch import RekeningCreateExtSch

class PemilikCreateSch(PemilikBase):
    kontaks:List[KontakCreateExtSch]
    rekenings:List[RekeningCreateExtSch]

class PemilikSch(PemilikFullBase):
    pass

class PemilikByIdSch(PemilikFullBase):
    kontaks:List[Kontak]
    rekenings:List[Rekening]

@optional
class PemilikUpdateSch(PemilikBase):
    pass

