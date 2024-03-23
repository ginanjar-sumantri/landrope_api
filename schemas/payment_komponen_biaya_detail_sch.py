from models.payment_model import PaymentKomponenBiayaDetailBase, PaymentKomponenBiayaDetailFullBase
from sqlmodel import SQLModel
from common.partial import optional
from decimal import Decimal
from sqlmodel import Field
from uuid import UUID
from datetime import date


class PaymentKomponenBiayaDetailCreateSch(PaymentKomponenBiayaDetailBase):
    pass

class PaymentKomponenBiayaDetailExtSch(SQLModel):
    beban_biaya_id: UUID
    giro_id: UUID | None
    giro_index: UUID | None
    amount: Decimal | None 


class PaymentKomponenBiayaDetailSch(PaymentKomponenBiayaDetailFullBase):
    pass

@optional
class PaymentKomponenBiayaDetailUpdateSch(PaymentKomponenBiayaDetailBase):
    pass