from models.payment_model import Payment, PaymentBase, PaymentFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class PaymentCreateSch(PaymentBase):
    pass

class PaymentSch(PaymentFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

@optional
class PaymentUpdateSch(PaymentBase):
    pass