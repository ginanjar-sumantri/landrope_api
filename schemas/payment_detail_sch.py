from models.payment_model import PaymentDetail, PaymentDetailBase, PaymentDetailFullBase
from common.partial import optional
from common.as_form import as_form
from common.enum import PaymentMethodEnum, JenisBayarEnum
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID
from datetime import date

class PaymentDetailCreateSch(PaymentDetailBase):
    pass

class PaymentDetailExtSch(SQLModel):
    id:UUID|None
    invoice_id:UUID|None
    amount:Decimal|None
    allocation_date:date|None
    giro_id: UUID | None
    id_index: UUID | None
    realisasi: bool | None

class PaymentDetailSch(PaymentDetailFullBase):
    code_giro:str | None = Field(alias="code_giro")
    nomor_giro:str | None = Field(alias="nomor_giro")
    payment_method:PaymentMethodEnum | None = Field(alias="payment_method")
    payment_date:date | None = Field(alias="payment_date")
    updated_by_name:str|None = Field(alias="updated_by_name")
    void_by_name:str|None = Field(alias="void_by_name")
    id_bidang:str|None = Field(alias="id_bidang")
    alashak:str|None = Field(alias="alashak")
    jenis_bayar:JenisBayarEnum|None = Field(alias="jenis_bayar")
    nomor_tahap:int|None = Field(alias="nomor_tahap")
    nomor_memo:str|None = Field(alias="nomor_memo")
    code_termin:str|None = Field(alias="code_termin")
    invoice_code:str|None = Field(alias="invoice_code")
    planing_name:str|None = Field(alias="planing_name")
    ptsk_name:str|None = Field(alias="ptsk_name")
    invoice_amount:Decimal|None = Field(alias="invoice_amount")
    luas_bayar:Decimal|None = Field(alias="luas_bayar")
    invoice_outstanding:Decimal|None = Field(alias="invoice_outstanding")
    giro_id: UUID | None
    payment_code: str | None

class PaymentDetailForPrintout(SQLModel):
    no:int|None
    payment_method:str|None
    amount:Decimal|None
    pay_to:str|None
    code:str|None
    amountExt:str|None

@optional
class PaymentDetailUpdateSch(PaymentDetailBase):
    pass