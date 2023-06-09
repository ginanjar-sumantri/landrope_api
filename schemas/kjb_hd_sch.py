from models.kjb_model import KjbHdBase, KjbHdFullBase, KjbRekening, KjbCaraBayar, KjbBebanBiaya, KjbDt
from schemas.kjb_rekening_sch import KjbRekeningCreateExtSch
from schemas.kjb_cara_bayar_sch import KjbCaraBayarCreateExtSch
from schemas.kjb_beban_biaya_sch import KjbBebanBiayaCreateExtSch
from common.partial import optional
from sqlmodel import Field
from typing import List

class KjbHdCreateSch(KjbHdBase):
    rekenings:List[KjbRekeningCreateExtSch]
    carabayars:List[KjbCaraBayarCreateExtSch]
    bebanbiayas:List[KjbBebanBiayaCreateExtSch]

class KjbHdSch(KjbHdFullBase):
    pass

class KjbHdByIdSch(KjbHdFullBase):
    kjb_dts:List[KjbDt]
    rekenings:List[KjbRekening]
    carabayars:List[KjbCaraBayar]
    bebanbiayas:List[KjbBebanBiaya]

    desa_name:str = Field(alias="desa_name")
    manager_name:str = Field(alias="manager_name")
    sales_name:str = Field(alias="sales_name")

    nomor_telepon:List[str] = Field(alias="nomor_telepon")



@optional
class KjbHdUpdateSch(KjbHdBase):
    pass