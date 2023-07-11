from models.bidang_model import BidangBase, BidangRawBase, BidangFullBase, BidangExtBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field
from pydantic import BaseModel
from decimal import Decimal

@as_form
class BidangCreateSch(BidangExtBase):
    pass

class BidangRawSch(BidangRawBase):
    planing_name:str|None = Field(alias='planing_name')
    project_name:str|None = Field(alias='project_name')
    desa_name:str|None = Field(alias='desa_name')
    section_name:str|None = Field(alias='section_name')
    ptsk_name:str|None = Field(alias='ptsk_name')
    nomor_sk:str|None = Field(alias='nomor_sk')
    id_rincik:str|None = Field(alias='id_rincik')
    jenis_lahan_name:str | None = Field(alias='jenis_lahan_name')
    
class BidangExtSch(BidangFullBase):
    planing:str|None 
    project:str|None
    desa:str|None 
    section:str|None 
    pt:str|None 
    nomor_sk:str|None 
    jenis_lahan:str | None
    tipeproses:str | None
    tipebidang:str | None
    jnsdokumen:str | None

class BidangSch(BidangFullBase):pass

class BidangShpSch(BaseModel):
    n_idbidang:str | None
    o_idbidang:str | None
    pemilik:str | None
    code_desa:str | None
    dokumen:str | None
    sub_surat:str | None
    alashak:str | None
    luassurat:Decimal | None
    kat:str | None
    kat_bidang:str | None
    ptsk:str | None
    penampung:str | None
    no_sk:str | None
    status_sk:str | None
    manager:str | None
    sales:str | None
    mediator:str | None
    proses:str | None
    status:str | None
    group:str | None
    no_peta:str | None
    desa:str | None
    project:str | None

@as_form
@optional
class BidangUpdateSch(BidangExtBase):
    pass