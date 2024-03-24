from models.payment_model import PaymentGiroDetailBase, PaymentGiroDetailFullBase
from sqlmodel import SQLModel
from common.partial import optional
from common.enum import PaymentMethodEnum
from decimal import Decimal
from sqlmodel import Field
from uuid import UUID
from datetime import date


class PaymentGiroDetailCreateSch(PaymentGiroDetailBase):
    pass

class PaymentGiroDetailExtSch(SQLModel):
    id:UUID | None
    giro_id: UUID | None
    id_index: UUID | None
    nomor_giro: str | None
    tanggal_buka: date | None
    tanggal_cair: date | None
    bank_code: str | None
    payment_date: date | None
    amount: Decimal | None
    payment_method: PaymentMethodEnum | None


class PaymentGiroDetailSch(PaymentGiroDetailFullBase):
    giro_code:str|None = Field(alias="giro_code")
    nomor_giro:str|None = Field(alias="nomor_giro")
    bank_code:str|None
    tanggal_buka:date|None
    tanggal_cair:date|None

@optional
class PaymentGiroDetailUpdateSch(PaymentGiroDetailBase):
    pass