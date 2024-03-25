from models.payment_model import Payment, PaymentBase, PaymentFullBase
from schemas.payment_detail_sch import PaymentDetailSch, PaymentDetailExtSch
from schemas.payment_giro_detail_sch import PaymentGiroDetailExtSch, PaymentGiroDetailSch
from schemas.payment_komponen_biaya_detail_sch import PaymentKomponenBiayaDetailExtSch, PaymentKomponenBiayaDetailSch
from schemas.beban_biaya_sch import BebanBiayaGroupingSch
from common.partial import optional
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID
from datetime import date

class PaymentCreateSch(PaymentBase):
    # nomor_giro:str|None
    # tanggal:date|None
    # tanggal_buka:date|None
    # tanggal_cair:date|None
    details:list[PaymentDetailExtSch]|None
    giros:list[PaymentGiroDetailExtSch]|None
    komponens:list[PaymentKomponenBiayaDetailExtSch]|None

class PaymentSch(PaymentFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")
    giro_code:str|None = Field(alias="giro_code")
    nomor_giro:str|None = Field(alias="nomor_giro")
    payment_outstanding:Decimal|None = Field(alias="payment_outstanding")
    tanggal_buka:date|None
    tanggal_cair:date|None
    nomor_memo:str|None
    pay_to_giros:str | None
    total_memo:Decimal | None
    total_komponen:Decimal | None

class PaymentByIdSch(PaymentFullBase):
    giro_code:str|None = Field(alias="giro_code")
    nomor_giro:str|None = Field(alias="nomor_giro")
    payment_outstanding:Decimal|None = Field(alias="payment_outstanding")
    details:list[PaymentDetailSch]
    giros:list[PaymentGiroDetailSch]
    komponens:list[BebanBiayaGroupingSch] | None
    tanggal_buka:date|None
    tanggal_cair:date|None

class PaymentVoidSch(SQLModel):
    void_reason:str

class PaymentDetailVoidSch(SQLModel):
    id:UUID
    void_reason:str

class PaymentVoidExtSch(SQLModel):
    details:list[PaymentDetailVoidSch]

@optional
class PaymentUpdateSch(PaymentBase):
    tanggal:date|None
    tanggal:date|None
    tanggal_buka:date|None
    tanggal_cair:date|None
    nomor_giro:str|None
    details:list[PaymentDetailExtSch]|None
    giros:list[PaymentGiroDetailExtSch]|None
    komponens:list[PaymentKomponenBiayaDetailExtSch]|None

