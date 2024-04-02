from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import PaymentMethodEnum, JenisBayarEnum
from decimal import Decimal
from datetime import date
import numpy

if TYPE_CHECKING:
    from models import Giro, Worker, Invoice, InvoiceDetail, BebanBiaya, Termin

class PaymentBase(SQLModel):
    payment_method:PaymentMethodEnum | None = Field(nullable=True)
    amount:Decimal | None = Field(nullable=True)
    giro_id:Optional[UUID] = Field(foreign_key="giro.id", nullable=True)
    bank_code:Optional[str] = Field(nullable=True)
    code:Optional[str] = Field(nullable=True)
    pay_to: str | None = Field(nullable=True)
    remark:str | None = Field(nullable=True)
    payment_date: date | None = Field(nullable=True)
    reference:str|None = Field(nullable=True)
    is_void:Optional[bool] = Field(nullable=True, default=False)
    void_by_id:Optional[UUID] = Field(foreign_key="worker.id", nullable=True)
    void_reason:Optional[str] = Field(nullable=True)
    void_at:Optional[date] = Field(nullable=True)

class PaymentFullBase(BaseUUIDModel, PaymentBase):
    pass

class Payment(PaymentFullBase, table=True):
    details:list["PaymentDetail"] = Relationship(
        back_populates="payment",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    giros:list["PaymentGiroDetail"] = Relationship(
        back_populates="payment",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    komponens:list["PaymentKomponenBiayaDetail"] = Relationship(
        back_populates="payment",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    giro:"Giro" = Relationship(
        back_populates="payment",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Payment.updated_by_id==Worker.id",
        }
    )

    worker_do_void: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Payment.void_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def giro_code(self) -> Decimal | None:
        return getattr(getattr(self, "giro", None), "code", None)
    
    @property
    def nomor_giro(self) -> str | None:
        if self.giro:
            return getattr(getattr(self, "giro", None), "nomor_giro", None)
        else:
            nomor_giro_ = []
            for giro in self.giros:
                nomor_giro = giro.nomor_giro if giro.payment_method != PaymentMethodEnum.Tunai else "Tunai"
                if nomor_giro not in nomor_giro_:
                    nomor_giro_.append(nomor_giro or "")
            
            return ",".join(nomor_giro_)
        
    @property
    def nomor_memo(self) -> str | None:
        nomor_memo_ = []
        for dt in self.details:
            nomor = getattr(getattr(getattr(dt, "invoice", None), "termin", None), "nomor_memo", None)
            if nomor:
                if nomor not in nomor_memo_:
                    nomor_memo_.append(nomor)
        
        return ",".join(nomor_memo_)
    
    @property
    def pay_to_giros(self) -> str | None:
        
        if self.pay_to:
            return self.pay_to

        pay_to_ = []
        for giro in self.giros:
            pay_to_.append(giro.pay_to)
        
        return ",".join(pay_to_)
    
    @property
    def bank_code(self) -> str | None:
        return getattr(getattr(self, "giro", None), "bank_code", None)
    
    @property
    def tanggal_buka(self) -> date | None:
        return getattr(getattr(self, "giro", None), "tanggal_buka", None)
    
    @property
    def tanggal_cair(self) -> date | None:
        return getattr(getattr(self, "giro", None), "tanggal_cair", None)
    
    @property
    def payment_outstanding(self) -> Decimal | None:
        total_payment:Decimal = 0
        if len(self.details) > 0:
            array_payment = [payment_dtl.amount for payment_dtl in self.details if payment_dtl.is_void != True]
            total_payment = sum(array_payment)
        
        if self.giro:
            amount = self.amount
        else:
            amount = sum([giro.amount for giro in self.giros])

        return Decimal(amount - total_payment)
        
        # return Decimal((self.amount or 0) - total_payment)
    
    @property
    def total_memo(self) -> Decimal | None:
        return sum([dt.amount for dt in self.details if dt.is_void != True])
    
    @property
    def total_komponen(self) -> Decimal | None:
        return sum([dt.amount for dt in self.komponens])


class PaymentGiroDetailBase(SQLModel):
    payment_id: UUID | None = Field(foreign_key="payment.id", nullable=False)
    payment_method: PaymentMethodEnum | None = Field(nullable=False)
    giro_id: UUID | None = Field(foreign_key="giro.id", nullable=True)
    amount: Decimal = Field(nullable=True, default=0)
    pay_to: str | None = Field(nullable=True)

class PaymentGiroDetailFullBase(BaseUUIDModel, PaymentGiroDetailBase):
    pass

class PaymentGiroDetail(PaymentGiroDetailFullBase, table=True):
    payment: "Payment" = Relationship(
        back_populates="giros",
        sa_relationship_kwargs={
        "lazy":"select"
    })

    giro: "Giro" = Relationship(
        back_populates="payment_giros",
        sa_relationship_kwargs=
        {
            "lazy":"select"
        }
    )

    payment_details: list["PaymentDetail"] = Relationship(
        back_populates="payment_giro",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    payment_komponen_biaya_details: list["PaymentKomponenBiayaDetail"] = Relationship(
        back_populates="payment_giro",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    @property
    def giro_code(self) -> Decimal | None:
        return getattr(getattr(self, "giro", None), "code", None)
    
    @property
    def nomor_giro(self) -> str | None:
        return getattr(getattr(self, "giro", None), "nomor_giro", None)
    
    @property
    def bank_code(self) -> str | None:
        return getattr(getattr(self, "giro", None), "bank_code", None)
    
    @property
    def tanggal_buka(self) -> date | None:
        return getattr(getattr(self, "giro", None), "tanggal_buka", None)
    
    @property
    def tanggal_cair(self) -> date | None:
        return getattr(getattr(self, "giro", None), "tanggal_cair", None)


class PaymentDetailBase(SQLModel):
    payment_id:UUID = Field(foreign_key="payment.id")
    invoice_id:UUID = Field(foreign_key="invoice.id")
    amount:Decimal = Field(default=0, nullable=True)
    is_void:Optional[bool] = Field(default=False, nullable=False)
    void_by_id:Optional[UUID] = Field(foreign_key="worker.id", nullable=True)
    remark:Optional[str] = Field(nullable=True)
    void_reason:Optional[str] = Field(nullable=True)
    void_at:Optional[date] = Field(nullable=True)
    allocation_date:Optional[date] = Field(nullable=True)
    payment_giro_detail_id: UUID | None = Field(foreign_key="payment_giro_detail.id", nullable=True)
    realisasi:bool | None = Field(nullable=True, default=False)

class PaymentDetailFullBase(BaseUUIDModel, PaymentDetailBase):
    pass

class PaymentDetail(PaymentDetailFullBase, table=True):
    payment:"Payment" = Relationship(
        back_populates="details",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    invoice:"Invoice" = Relationship(
        back_populates="payment_details",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    payment_giro:"PaymentGiroDetail" = Relationship(
        back_populates="payment_details",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    worker_do_void: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "PaymentDetail.void_by_id==Worker.id",
        }
    )

    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "PaymentDetail.updated_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def void_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker_do_void', None), 'name', None)
    
    @property
    def code_giro(self) -> str | None:
        if self.payment.giro:
            return self.payment.giro.code
        else:
            return getattr(getattr(getattr(self, "payment_giro", None), "giro", None), "code")
        
        return self.payment.code
    
    @property
    def nomor_giro(self) -> str | None:
        if self.payment.giro:
            return self.payment.giro.nomor_giro
        else:
            return getattr(getattr(getattr(self, "payment_giro", None), "giro", None), "nomor_giro")
        
        return None
    
    @property
    def payment_method(self) -> PaymentMethodEnum | None:
        if self.payment.payment_method:
            return getattr(getattr(self, "payment", None), "payment_method", None)
        else:
            return getattr(getattr(getattr(self, "payment_giro", None), "giro", None), "payment_method")

    @property
    def payment_date(self) -> date | None:
        return getattr(getattr(self, "payment", None), "payment_date", None)
    
    @property
    def payment_code(self) -> str | None:
        return getattr(getattr(self, "payment", None), "code", None)
    
    @property
    def id_bidang(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "id_bidang", None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "ptsk_name", None)
    
    @property
    def planing_name(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "planing_name", None)
    
    @property
    def invoice_outstanding(self) -> Decimal | None:
        return getattr(getattr(self, "invoice", None), "invoice_outstanding", None)
    
    @property
    def invoice_code(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "code", None)
    
    @property
    def alashak(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "alashak", None)
    
    @property
    def jenis_bayar(self) -> JenisBayarEnum | None:
        return getattr(getattr(self, "invoice", None), "jenis_bayar", None)
    
    @property
    def nomor_memo(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "nomor_memo", None)
    
    @property
    def code_memo(self) -> str | None:
        return getattr(getattr(self, "invoice", None), "code_memo", None)
    
    @property
    def nomor_tahap(self) -> int | None:
        return getattr(getattr(self, "invoice", None), "nomor_tahap", None)
    
    @property
    def invoice_amount(self) -> Decimal | None:
        return getattr(getattr(self, "invoice", None), "amount", None)
    
    @property
    def luas_bayar(self) -> Decimal | None:
        return getattr(getattr(getattr(self, "invoice", None), "bidang", None), "luas_bayar")
    
    @property
    def giro_id(self) -> UUID | None:
        return getattr(getattr(self, "payment_giro", None), "giro_id", None)

    
class PaymentKomponenBiayaDetailBase(SQLModel):
    payment_id: UUID = Field(foreign_key="payment.id", nullable=False)
    invoice_detail_id: UUID = Field(foreign_key="invoice_detail.id")
    payment_giro_detail_id: UUID = Field(foreign_key="payment_giro_detail.id", nullable=False)
    beban_biaya_id: UUID = Field(foreign_key="beban_biaya.id", nullable=False)
    amount: Decimal = Field(nullable=False, default=0)

class PaymentKomponenBiayaDetailFullBase(BaseUUIDModel, PaymentKomponenBiayaDetailBase):
    pass

class PaymentKomponenBiayaDetail(PaymentKomponenBiayaDetailFullBase, table=True):
    payment:"Payment" = Relationship(
        back_populates="komponens",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    invoice_detail:"InvoiceDetail" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    payment_giro:"PaymentGiroDetail" = Relationship(
        back_populates="payment_komponen_biaya_details",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    beban_biaya:"BebanBiaya" = Relationship(
        sa_relationship_kwargs={
            "lazy" : "select"
        }
    )

    @property
    def beban_biaya_name(self) -> str | None:
        return getattr(getattr(self, "beban_biaya", None), "name", None)
    

    @property
    def memo_code(self) -> str | None:
        return getattr(getattr(getattr(getattr(self, "invoice_detail", None), "invoice", None), "termin", None), "code", None)
    
    @property
    def nomor_memo(self) -> str | None:
        return getattr(getattr(getattr(getattr(self, "invoice_detail", None), "invoice", None), "termin", None), "nomor_memo", None)
    
    @property
    def termin_id(self) -> str | None:
        return getattr(getattr(getattr(getattr(self, "invoice_detail", None), "invoice", None), "termin", None), "id", None)
    
    @property
    def giro_id(self) -> Decimal | None:
        return getattr(getattr(self, "payment_giro", None), "giro_id", None)
    
    @property
    def nomor_giro(self) -> Decimal | None:
        return getattr(getattr(self, "payment_giro", None), "nomor_giro", None)