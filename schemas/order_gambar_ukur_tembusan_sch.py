from models.order_gambar_ukur_model import OrderGambarUkurTembusan, OrderGambarUkurTembusanBase, OrderGambarUkurTembusanFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class OrderGambarUkurTembusanCreateSch(OrderGambarUkurTembusanBase):
    pass

class OrderGambarUkurTembusanSch(OrderGambarUkurTembusanFullBase):
    pass

@optional
class OrderGambarUkurTembusanUpdateSch(OrderGambarUkurTembusanBase):
    pass