from models.payment_model import PaymentDetail, PaymentDetailBase, PaymentDetailFullBase
from common.partial import optional
from common.as_form import as_form
from common.enum import PaymentMethodEnum, JenisBayarEnum
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID

class PaymentDetailCreateSch(PaymentDetailBase):
    pass

class PaymentDetailExtSch(SQLModel):
    id:UUID|None
    invoice_id:UUID|None
    amount:Decimal|None

class PaymentDetailSch(PaymentDetailFullBase):
    code_giro:str | None = Field(alias="code_giro")
    payment_method:PaymentMethodEnum | None = Field(alias="payment_method")
    updated_by_name:str|None = Field(alias="updated_by_name")
    void_by_name:str|None = Field(alias="void_by_name")
    id_bidang:str|None = Field(alias="id_bidang")
    alashak:str|None = Field(alias="alashak")
    jenis_bayar:JenisBayarEnum|None = Field(alias="jenis_bayar")
    nomor_tahap:int|None = Field(alias="nomor_tahap")
    nomor_memo:str|None = Field(alias="nomor_memo")
    code_termin:str|None = Field(alias="code_termin")

@optional
class PaymentDetailUpdateSch(PaymentDetailBase):
    pass