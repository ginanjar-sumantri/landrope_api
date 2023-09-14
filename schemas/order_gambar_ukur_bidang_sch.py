from models.order_gambar_ukur_model import OrderGambarUkurBidang, OrderGambarUkurBidangBase, OrderGambarUkurBidangFullBase
from common.partial import optional
from common.as_form import as_form
from common.enum import JenisAlashakEnum, HasilAnalisaPetaLokasiEnum, ProsesBPNOrderGambarUkurEnum
from sqlmodel import SQLModel, Field
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal

class OrderGambarUkurBidangCreateSch(OrderGambarUkurBidangBase):
    pass

class OrderGambarUkurBidangSch(OrderGambarUkurBidangFullBase):
    id_bidang:str | None = Field(alias="id_bidang")
    jenis_alashak:JenisAlashakEnum | None = Field(alias="jenis_alashak")
    alashak:str | None = Field(alias="alashak")
    luas_surat:Decimal | None = Field(alias="luas_surat")
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum  | None = Field(alias="hasil_analisa_peta_lokasi")
    proses_bpn_order_gu:ProsesBPNOrderGambarUkurEnum | None = Field(alias="proses_bpn_order_gu")

class OrderGambarUkurBidangPdfSch(SQLModel):
    no:int | None
    id_bidang:str | None 
    pemilik_name:str | None 
    group:str | None 
    ptsk_name:str | None 
    jenis_surat_name:str | None 
    alashak:str | None 
    luas_surat:str | None
    mediator:str | None
    sales_name:str | None 
    
class OrderGambarUkurBidangRawSch(SQLModel):
    id:UUID | None
    bidang_id:UUID | None

@optional
class OrderGambarUkurBidangUpdateSch(OrderGambarUkurBidangBase):
    pass