from models.request_peta_lokasi import RequestPetaLokasiBase, RequestPetaLokasiFullBase
from common.partial import optional
from sqlmodel import Field
from typing import List
from decimal import Decimal

class RequestPetaLokasiCreateSch(RequestPetaLokasiBase):
    pass

class RequestPetaLokasiSch(RequestPetaLokasiFullBase):
    kjb_hd_code:str = Field(alias="kjb_hd_code")
    mediator:str = Field(alias="mediator")
    group:str = Field(alias="group")
    nama_pemilik_tanah:str = Field(alias="nama_pemilik_tanah")
    nomor_pemilik_tanah:str = Field(alias="nomor_pemilik_tanah")
    luas:Decimal = Field(alias="luas")
    desa_name:str = Field(alias="desa_name")
    project_name:str = Field(alias="project_name")

@optional
class RequestPetaLokasiUpdateSch(RequestPetaLokasiBase):
    pass