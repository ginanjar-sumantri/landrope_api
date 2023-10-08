from models.payment_model import Payment, PaymentBase, PaymentFullBase
from schemas.payment_detail_sch import PaymentDetailSch, PaymentDetailExtSch
from common.partial import optional
from sqlmodel import SQLModel, Field
from decimal import Decimal

class PaymentCreateSch(PaymentBase):
    details:list[PaymentDetailExtSch]|None

class PaymentSch(PaymentFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")
    giro_outstanding:Decimal|None = Field(alias="giro_outstanding")
    payment_outstanding:Decimal|None = Field(alias="payment_outstanding")

class PaymentByIdSch(PaymentFullBase):
    giro_outstanding:Decimal|None = Field(alias="giro_outstanding")
    payment_outstanding:Decimal|None = Field(alias="payment_outstanding")
    details:list[PaymentDetailSch]

@optional
class PaymentUpdateSch(PaymentBase):
    details:list[PaymentDetailExtSch]|None