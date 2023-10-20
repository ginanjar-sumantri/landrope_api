from models.payment_model import Payment, PaymentBase, PaymentFullBase
from schemas.payment_detail_sch import PaymentDetailSch, PaymentDetailExtSch
from common.partial import optional
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID

class PaymentCreateSch(PaymentBase):
    nomor_giro:str|None
    details:list[PaymentDetailExtSch]|None

class PaymentSch(PaymentFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")
    giro_code:str|None = Field(alias="giro_code")
    nomor_giro:str|None = Field(alias="nomor_giro")
    payment_outstanding:Decimal|None = Field(alias="payment_outstanding")

class PaymentByIdSch(PaymentFullBase):
    giro_code:str|None = Field(alias="giro_code")
    nomor_giro:str|None = Field(alias="nomor_giro")
    payment_outstanding:Decimal|None = Field(alias="payment_outstanding")
    details:list[PaymentDetailSch]

class PaymentVoidSch(SQLModel):
    remark:str

class PaymentDetailVoidSch(SQLModel):
    id:UUID
    remark:str

class PaymentVoidExtSch(SQLModel):
    details:list[PaymentDetailVoidSch]

@optional
class PaymentUpdateSch(PaymentBase):
    nomor_giro:str|None
    details:list[PaymentDetailExtSch]|None