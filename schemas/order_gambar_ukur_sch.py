from models.order_gambar_ukur_model import OrderGambarUkur, OrderGambarUkurBase, OrderGambarUkurFullBase
from schemas.order_gambar_ukur_bidang_sch import OrderGambarUkurBidangCreateSch, OrderGambarUkurBidangRawSch
from schemas.order_gambar_ukur_tembusan_sch import OrderGambarUkurTembusanCreateSch, OrderGambarUkurTembusanRawSch
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class OrderGambarUkurCreateSch(OrderGambarUkurBase):
    bidangs:list[OrderGambarUkurBidangCreateSch]
    tembusans:list[OrderGambarUkurTembusanCreateSch]

class OrderGambarUkurSch(OrderGambarUkurFullBase):
    pass

@optional
class OrderGambarUkurUpdateSch(OrderGambarUkurBase):
    bidangs:list[OrderGambarUkurBidangRawSch]
    tembusans:list[OrderGambarUkurTembusanRawSch]