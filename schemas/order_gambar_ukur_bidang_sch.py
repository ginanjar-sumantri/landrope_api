from models.order_gambar_ukur_model import OrderGambarUkurBidang, OrderGambarUkurBidangBase, OrderGambarUkurBidangFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime
from uuid import UUID

class OrderGambarUkurBidangCreateSch(OrderGambarUkurBidangBase):
    pass

class OrderGambarUkurBidangSch(OrderGambarUkurBidangFullBase):
    pass

class OrderGambarUkurBidangRawSch(SQLModel):
    id:UUID | None
    bidang_id:UUID | None

@optional
class OrderGambarUkurBidangUpdateSch(OrderGambarUkurBidangBase):
    pass