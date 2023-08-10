from models.request_peta_lokasi_model import RequestPetaLokasiBase, RequestPetaLokasiFullBase
from common.partial import optional
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
    desa_name:str | None = Field(alias="desa_name")
    mediator:str | None = Field(alias="mediator")
    group:str | None = Field(alias="group")
    kjb_hd_code:str | None = Field(alias="kjb_hd_code")

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

class RequestPetaLokasiSch(RequestPetaLokasiFullBase):
    kjb_hd_code:str | None = Field(alias="kjb_hd_code")
    mediator:str | None = Field(alias="mediator")
    group:str | None = Field(alias="group")
    nama_pemilik_tanah:str  | None= Field(alias="nama_pemilik_tanah")
    nomor_pemilik_tanah:str | None = Field(alias="nomor_pemilik_tanah")
    luas:Decimal | None = Field(alias="luas")
    desa_name:str | None = Field(alias="desa_name")
    project_name:str | None = Field(alias="project_name")
    alashak:str | None = Field(alias="alashak")
    updated_by_name:str|None = Field(alias="updated_by_name")

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