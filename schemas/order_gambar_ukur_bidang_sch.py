from models.order_gambar_ukur_model import OrderGambarUkurBidang, OrderGambarUkurBidangBase, OrderGambarUkurBidangFullBase
from common.partial import optional
from common.as_form import as_form
from common.enum import JenisAlashakEnum, HasilAnalisaPetaLokasiEnum, ProsesBPNOrderGambarUkurEnum
from sqlmodel import SQLModel, Field
from datetime import date, datetime
from uuid import UUID

class OrderGambarUkurBidangCreateSch(OrderGambarUkurBidangBase):
    pass

class OrderGambarUkurBidangSch(OrderGambarUkurBidangFullBase):
    id_bidang:UUID | None = Field(alias="id_bidang")
    jenis_alashak:JenisAlashakEnum | None = Field(alias="jenis_alashak")
    alashak:str | None = Field(alias="alashak")
    hasil_analisa_peta_lokasi:HasilAnalisaPetaLokasiEnum  | None = Field(alias="hasil_analisa_peta_lokasi")
    proses_bpn_order_gu:ProsesBPNOrderGambarUkurEnum | None = Field(alias="proses_bpn_order_gu")

class OrderGambarUkurBidangRawSch(SQLModel):
    id:UUID | None
    bidang_id:UUID | None

@optional
class OrderGambarUkurBidangUpdateSch(OrderGambarUkurBidangBase):
    pass