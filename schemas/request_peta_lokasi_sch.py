from models.request_peta_lokasi_model import RequestPetaLokasiBase, RequestPetaLokasiFullBase
from common.partial import optional
from common.enum import HasilAnalisaPetaLokasiEnum, StatusHasilPetaLokasiEnum
from sqlmodel import Field, SQLModel
from typing import List
from decimal import Decimal
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date


class RequestPetaLokasiCreateSch(RequestPetaLokasiBase):
    pass

class RequestPetaLokasiCreatesSch(BaseModel):
    tanggal:date | None
    kjb_dt_ids: List[UUID]
    remark:str | None

class RequestPetaLokasiHdSch(SQLModel):
    code:str | None
    desa_name:str | None
    mediator:str | None
    group:str | None 
    kjb_hd_code:str | None
    updated_at:datetime|None

class RequestPetaLokasiHdbyCodeSch(BaseModel):
    code:str | None
    desa_name:str | None 
    mediator:str | None 
    group:str | None
    tanggal:date | None
    remark:str | None
    kjb_hd_code:str | None 
    kjb_hd_id:UUID | None
    kjb_dt_ids: List[UUID]

class RequestPetaLokasiForInputHasilSch(SQLModel):
    id:UUID
    code:str | None
    alashak:str | None
    pemilik_name:str | None
    kjb_hd_code:str | None
    mediator:str | None
    id_bidang:str | None
    bidang_id:UUID | None
    file_path:str | None
    kjb_dt_id:UUID | None
    hasil_peta_lokasi_id:UUID | None
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum | None
    status_hasil_peta_lokasi:StatusHasilPetaLokasiEnum | None
    remark:str | None

class RequestPetaLokasiSch(RequestPetaLokasiFullBase):
    alashak:str | None
    pemilik_name:str | None
    kjb_hd_code:str | None
    mediator:str | None
    id_bidang:str | None
    bidang_id:UUID | None
    file_path:str | None


class RequestPetaLokasiPdfSch(BaseModel):
    no:str | None
    mediator:str | None
    group:str | None
    pemilik:str | None
    no_pemilik:str | None
    alashak:str | None
    luas:str | None
    desa:str|None
    project:str|None
    remark:str|None

@optional
class RequestPetaLokasiUpdateSch(RequestPetaLokasiBase):
    kjb_dt_ids: List[UUID]
    remark:str | None

@optional
class RequestPetaLokasiUpdateExtSch(BaseModel):
    code:str = Field(nullable=True)
    tanggal:date = Field(default=date.today(), nullable=False)
    kjb_dt_ids: List[UUID]
    remark:str | None