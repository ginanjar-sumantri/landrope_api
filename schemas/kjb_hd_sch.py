from models.kjb_model import KjbHdBase, KjbHdFullBase
from schemas.kjb_dt_sch import KjbDtSch, KjbDtForUtjKhususSch
from schemas.kjb_termin_sch import KjbTerminSch
from schemas.kjb_rekening_sch import KjbRekeningCreateExtSch, KjbRekeningSch
from schemas.kjb_harga_sch import KjbHargaCreateExtSch, KjbHargaExtSch
from schemas.kjb_beban_biaya_sch import KjbBebanBiayaCreateExtSch, KjbBebanBiayaSch
from schemas.kjb_penjual_sch import KjbPenjualCreateExtSch, KjbPenjualSch
from schemas.kjb_dt_sch import KjbDtCreateExtSch
from schemas.bidang_sch import BidangForUtjSch
from common.partial import optional
from common.enum import KategoriPenjualEnum
from sqlmodel import Field, SQLModel 
from typing import List, Optional
from decimal import Decimal
from uuid import UUID

class KjbHdCreateSch(KjbHdBase):
    rekenings:List[KjbRekeningCreateExtSch] | None
    hargas:List[KjbHargaCreateExtSch] | None
    bebanbiayas:List[KjbBebanBiayaCreateExtSch] | None
    penjuals:List[KjbPenjualCreateExtSch] | None
    details:List[KjbDtCreateExtSch] | None
    file:str|None


class KjbHdSch(KjbHdFullBase):
    desa_name:str = Field(alias="desa_name")
    manager_name:str = Field(alias="manager_name")
    sales_name:str = Field(alias="sales_name")
    total_luas_surat:Decimal = Field(alias="total_luas_surat")
    penjuals:List[KjbPenjualSch] | None
    updated_by_name:str|None = Field(alias="updated_by_name")
    status_workflow:str|None
    step_name_workflow:str|None
    

class KjbHdByIdSch(KjbHdFullBase):
    kjb_dts:List[KjbDtSch] | None
    rekenings:List[KjbRekeningSch] | None
    hargas:List[KjbHargaExtSch] | None
    bebanbiayas:List[KjbBebanBiayaSch] | None
    penjuals:List[KjbPenjualSch] | None
    
    desa_name:str = Field(alias="desa_name")
    manager_name:str = Field(alias="manager_name")
    sales_name:str = Field(alias="sales_name")
    total_luas_surat:Decimal = Field(alias="total_luas_surat")

    status_workflow:str|None
    step_name_workflow:str|None

class KjbHdSearchSch(SQLModel):
    id:UUID
    code:Optional[str]


@optional
class KjbHdUpdateSch(KjbHdCreateSch):
    pass

class KjbHdForTerminByIdSch(SQLModel):
    id:UUID
    code:Optional[str]
    nama_group:Optional[str]
    utj_amount:Optional[Decimal]
    bidangs:list[BidangForUtjSch] | None

class KjbHdForUtjKhususByIdSch(SQLModel):
    id:UUID
    code:Optional[str]
    nama_group:Optional[str]
    utj_amount:Optional[Decimal]
    kjb_dts:list[KjbDtForUtjKhususSch] | None

class KjbHdForCloud(SQLModel):
    id:UUID
    nama_group:Optional[str]
    manager_id:Optional[UUID]
    sales_id:Optional[UUID]
    mediator:Optional[str]
    telepon_mediator:Optional[str]
    kategori_penjual:Optional[KategoriPenjualEnum]