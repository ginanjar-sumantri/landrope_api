from models.order_gambar_ukur_model import OrderGambarUkurTembusan, OrderGambarUkurTembusanBase, OrderGambarUkurTembusanFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime
from uuid import UUID

class OrderGambarUkurTembusanCreateSch(OrderGambarUkurTembusanBase):
    pass

class OrderGambarUkurTembusanSch(OrderGambarUkurTembusanFullBase):
    cc_name:str | None = Field(alias="cc_name")

class OrderGambarUkurTembusanRawSch(SQLModel):
    id: UUID | None
    tembusan_id:UUID | None

@optional
class OrderGambarUkurTembusanUpdateSch(OrderGambarUkurTembusanBase):
    pass