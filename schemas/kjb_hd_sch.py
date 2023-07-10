from models.kjb_model import KjbHdBase, KjbHdFullBase
from schemas.kjb_dt_sch import KjbDtSch
from schemas.kjb_termin_sch import KjbTerminSch
from schemas.kjb_rekening_sch import KjbRekeningCreateExtSch, KjbRekeningSch
from schemas.kjb_harga_sch import KjbHargaCreateExtSch, KjbHargaExtSch
from schemas.kjb_beban_biaya_sch import KjbBebanBiayaCreateExtSch, KjbBebanBiayaSch
from schemas.kjb_penjual_sch import KjbPenjualCreateExtSch, KjbPenjualSch
from common.partial import optional
from sqlmodel import Field
from typing import List

class KjbHdCreateSch(KjbHdBase):
    rekenings:List[KjbRekeningCreateExtSch]
    hargas:List[KjbHargaCreateExtSch]
    bebanbiayas:List[KjbBebanBiayaCreateExtSch]
    penjuals:List[KjbPenjualCreateExtSch]

class KjbHdSch(KjbHdFullBase):
    desa_name:str = Field(alias="desa_name")
    manager_name:str = Field(alias="manager_name")
    sales_name:str = Field(alias="sales_name")
    

class KjbHdByIdSch(KjbHdFullBase):
    kjb_dts:List[KjbDtSch]
    rekenings:List[KjbRekeningSch]
    hargas:List[KjbHargaExtSch]
    bebanbiayas:List[KjbBebanBiayaSch]
    penjuals:List[KjbPenjualSch]

    desa_name:str = Field(alias="desa_name")
    manager_name:str = Field(alias="manager_name")
    sales_name:str = Field(alias="sales_name")


@optional
class KjbHdUpdateSch(KjbHdBase):
    pass