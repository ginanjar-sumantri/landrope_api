from models.order_gambar_ukur_model import OrderGambarUkur, OrderGambarUkurBase, OrderGambarUkurFullBase
from schemas.order_gambar_ukur_bidang_sch import OrderGambarUkurBidangCreateSch, OrderGambarUkurBidangRawSch, OrderGambarUkurBidangSch
from schemas.order_gambar_ukur_tembusan_sch import OrderGambarUkurTembusanCreateSch, OrderGambarUkurTembusanRawSch, OrderGambarUkurTembusanSch
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal

class OrderGambarUkurCreateSch(OrderGambarUkurBase):
    kjb_dts:list[UUID]
    tembusans:list[UUID]


class OrderGambarUkurSch(OrderGambarUkurFullBase):
    tujuan_surat:str | None = Field(alias="tujuan_surat")
    perihal:str | None = Field(alias="perihal")
    updated_by_name:str | None = Field(alias="updated_by_name")

class OrderGambarUkurByIdSch(OrderGambarUkurFullBase):
    tujuan_surat:str | None = Field(alias="tujuan_surat")
    bidangs:list[OrderGambarUkurBidangSch]
    tembusans:list[OrderGambarUkurTembusanSch]

@optional
class OrderGambarUkurUpdateSch(OrderGambarUkurBase):
    bidangs:list[UUID]
    tembusans:list[UUID]

@optional
class OrderGambarUkurUpdateExtSch(OrderGambarUkurBase):
    pass