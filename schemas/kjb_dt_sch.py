from models.kjb_model import KjbDt, KjbDtBase, KjbDtFullBase
from common.partial import optional
from common.enum import JenisAlashakEnum, PosisiBidangEnum, StatusPetaLokasiEnum
from sqlmodel import Field, SQLModel
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

class KjbDtCreateSch(KjbDtBase):
    pass

class KjbDtCreateExtSch(SQLModel):
    jenis_alashak:JenisAlashakEnum
    alashak:str
    posisi_bidang:PosisiBidangEnum
    harga_akta:Decimal
    harga_transaksi:Decimal
    luas_surat:Decimal
    desa_id:Optional[UUID] 
    project_id:Optional[UUID] 
    pemilik_id:UUID | None 
    jenis_surat_id:UUID | None 

class KjbDtSch(KjbDtFullBase):
    kjb_code:str | None = Field(alias="kjb_code")
    jenis_surat_name:str | None = Field(alias="jenis_surat_name")
    desa_name:str | None = Field(alias="desa_name")
    desa_name_by_ttn:str | None = Field(alias="desa_name_by_ttn")
    project_name:str | None = Field(alias="project_name")
    project_name_by_ttn:str | None = Field(alias="project_name_by_ttn")
    kategori_penjual:str | None = Field(alias="kategori_penjual")
    done_request_petlok:bool | None = Field(alias="done_request_petlok")
    pemilik_name:str | None = Field(alias="pemilik_name")
    nomor_telepon:List[str] | None = Field(alias="nomor_telepon")
    updated_by_name:str|None = Field(alias="updated_by_name")
    

@optional
class KjbDtUpdateSch(KjbDtBase):
    pass

class KjbDtSrcForGUSch(SQLModel):
    kjb_dt_id:UUID | None
    kjb_dt_alashak:str | None
    bidang_id:UUID | None
    id_bidang:str | None