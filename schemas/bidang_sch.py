from models.bidang_model import BidangBase, BidangRawBase, BidangFullBase, BidangExtBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field

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

@as_form
@optional
class BidangUpdateSch(BidangBase):
    pass