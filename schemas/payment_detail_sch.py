from models.payment_model import PaymentDetail, PaymentDetailBase, PaymentDetailFullBase
from common.partial import optional
from common.as_form import as_form
from common.enum import PaymentMethodEnum
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class PaymentDetailCreateSch(PaymentDetailBase):
    pass

class PaymentDetailSch(PaymentDetailFullBase):
    code:str | None = Field(alias="code")
    payment_method:PaymentMethodEnum | None = Field(alias="payment_method")
    
    updated_by_name:str|None = Field(alias="updated_by_name")
    void_by_name:str|None = Field(alias="void_by_name")



@optional
class PaymentDetailUpdateSch(PaymentDetailBase):
    pass