from models.bidang_model import BidangBase, BidangRawBase, BidangFullBase
from models.base_model import BaseGeoModel
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field
from pydantic import BaseModel
from decimal import Decimal

@as_form
class BidangCreateSch(BidangBase):
    pass

class BidangRawSch(BidangRawBase):
    pemilik_name:str|None = Field(alias='pemilik_name')
    project_name:str|None = Field(alias='project_name')
    desa_name:str|None = Field(alias='desa_name')

class BidangByIdSch(BidangRawBase):
    pemilik_name:str|None = Field(alias='pemilik_name')
    project_name:str|None = Field(alias='project_name')
    desa_name:str|None = Field(alias='desa_name')
    planing_name:str|None = Field(alias='planing_name')
    jenis_surat_name:str|None = Field(alias='jenis_surat_name')
    kategori_name:str|None = Field(alias='kategori_name')
    kategori_sub_name:str|None = Field(alias='kategori_sub_name')
    kategori_proyek_name:str|None = Field(alias='kategori_proyek_name')
    ptsk_name:str | None = Field(alias='ptsk_name')
    no_sk:str|None = Field(alias='no_sk')
    status_sk:str|None = Field(alias='status_sk')
    penampung_name:str|None = Field(alias='penampung_name')
    manager_name:str | None = Field(alias='manager_name')
    sales_name:str|None = Field(alias='sales_name')
    notaris_name:str | None = Field(alias='notaris_name')
    

class BidangSch(BidangFullBase):
    pass

class BidangShpSch(BaseGeoModel):
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
    kat_proyek:str | None
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

class BidangShpExSch(BaseGeoModel):
    n_idbidang:str | None
    o_idbidang:str | None
    pemilik:str | None
    code_desa:str | None
    dokumen:str | None
    sub_surat:str | None
    alashak:str | None
    luassurat:str | None
    kat:str | None
    kat_bidang:str | None
    kat_proyek:str | None
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
class BidangUpdateSch(BidangBase):
    pass