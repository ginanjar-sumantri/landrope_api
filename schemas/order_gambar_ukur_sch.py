from models.order_gambar_ukur_model import OrderGambarUkur, OrderGambarUkurBase, OrderGambarUkurFullBase
from schemas.order_gambar_ukur_bidang_sch import OrderGambarUkurBidangCreateSch, OrderGambarUkurBidangRawSch, OrderGambarUkurBidangSch
from schemas.order_gambar_ukur_tembusan_sch import OrderGambarUkurTembusanCreateSch, OrderGambarUkurTembusanRawSch, OrderGambarUkurTembusanSch
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime
from uuid import UUID

class OrderGambarUkurCreateSch(OrderGambarUkurBase):
    bidangs:list[UUID]
    tembusans:list[UUID]

class OrderGambarUkurSch(OrderGambarUkurFullBase):
    tujuan_surat:str | None = Field(alias="tujuan_surat")
    perihal:str | None = Field(alias="perihal")
    updated_by_name:str | None = Field(alias="updated_by_name")

class OrderGambarUkurByIdSch(OrderGambarUkurFullBase):
    tujuan_surat:str = Field(alias="tujuan_surat")
    bidangs:list[OrderGambarUkurBidangSch]
    tembusan:list[OrderGambarUkurTembusanSch]

@optional
class OrderGambarUkurUpdateSch(OrderGambarUkurBase):
    bidangs:list[OrderGambarUkurBidangRawSch]
    tembusans:list[OrderGambarUkurTembusanRawSch]