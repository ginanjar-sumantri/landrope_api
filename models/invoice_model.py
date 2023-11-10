from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import JenisBayarEnum, SatuanBayarEnum, SatuanHargaEnum
from decimal import Decimal
from datetime import date
from pydantic import condecimal
import numpy

if TYPE_CHECKING:
    from models import Worker, Termin, Spk, Bidang, BidangKomponenBiaya, PaymentDetail
    

class InvoiceBase(SQLModel):
    code:Optional[str] = Field(nullable=True)
    termin_id:Optional[UUID] = Field(foreign_key="termin.id", nullable=False)
    spk_id:Optional[UUID] = Field(foreign_key="spk.id", nullable=True)
    bidang_id:Optional[UUID] = Field(foreign_key="bidang.id", nullable=True)
    amount:Optional[Decimal] = Field(nullable=True, default=0)
    is_void:Optional[bool] = Field(nullable=True)
    remark:Optional[str] = Field(nullable=True)
    use_utj:Optional[bool] = Field(nullable=True, default=False)
    void_by_id:Optional[UUID] = Field(foreign_key="worker.id", nullable=True)
    void_reason:Optional[str] = Field(nullable=True)
    void_at:Optional[date] = Field(nullable=True)

class InvoiceFullBase(BaseUUIDModel, InvoiceBase):
    pass

class Invoice(InvoiceFullBase, table=True):
    termin:"Termin" = Relationship(
        back_populates="invoices",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    spk:"Spk" = Relationship(
        back_populates="invoices",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    bidang:"Bidang" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    details:list["InvoiceDetail"] = Relationship(
        back_populates="invoice",
        sa_relationship_kwargs=
        {
            "lazy" : "select",
            "cascade" : "delete, all",
             "foreign_keys" : "[InvoiceDetail.invoice_id]"
        }
    )

    payment_details:list["PaymentDetail"] = Relationship(
        back_populates="invoice",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )
    
    worker: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "select",
            "primaryjoin": "Invoice.updated_by_id==Worker.id",
        }
    )

    worker_do_void: "Worker" = Relationship(  
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "Invoice.void_by_id==Worker.id",
        }
    )

    @property
    def updated_by_name(self) -> str | None:
        return getattr(getattr(self, 'worker', None), 'name', None)
    
    @property
    def id_bidang(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "id_bidang", None)
    
    @property
    def luas_bayar(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "luas_bayar", None)
    
    @property
    def harga_transaksi(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "harga_transaksi", None)
    
    @property
    def group(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "group", None)
    
    @property
    def alashak(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "alashak", None)
    
    @property
    def ptsk_name(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "ptsk_name", None)
    
    @property
    def planing_name(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "planing_name", None)
    
    @property
    def jenis_bayar(self) -> JenisBayarEnum | None:
        return getattr(getattr(self, "termin", None), "jenis_bayar", None)
    
    @property
    def nomor_memo(self) -> str | None:
        return getattr(getattr(self, "termin", None), "nomor_memo", None)
    
    @property
    def code_termin(self) -> str | None:
        return getattr(getattr(self, "termin", None), "code", None)
    
    @property
    def nomor_tahap(self) -> int | None:
        return getattr(getattr(self, "termin", None), "nomor_tahap", None)
    
    @property
    def spk_code(self) -> Decimal | None:
        return getattr(getattr(self, "spk", None), "code", None)
    
    @property
    def spk_satuan_bayar(self) -> SatuanBayarEnum | None:
        return getattr(getattr(self, "spk", None), "satuan_bayar", None)
    
    #hasil perhitungan spk dengan luas bayar dan harga transaksi
    @property
    def spk_amount(self) -> Decimal | None:
        return getattr(getattr(self, "spk", None), "spk_amount", None)
    
    @property
    def amount_of_spk(self) -> Decimal | None:
        return getattr(getattr(self, "spk", None), "amount", None)
    
    @property
    def invoice_outstanding(self) -> Decimal | None:
        total_payment:Decimal = 0
        if len(self.payment_details) > 0:
            array_payment = [payment_dtl.amount for payment_dtl in self.payment_details if payment_dtl.is_void != True]
            total_payment = sum(array_payment)
        
        return Decimal(self.amount - Decimal(total_payment) - self.amount_beban - self.utj_amount)
    
    @property
    def amount_nett(self) -> Decimal | None:
        return Decimal(self.amount - self.amount_beban - self.utj_amount)
    
    @property
    def amount_beban(self) -> Decimal | None:
        amount_beban_biayas = [dt.amount_beban_penjual for dt in self.details]
        return sum(amount_beban_biayas)
    
    @property
    def has_payment(self) -> bool | None:
        active_payments = [x for x in self.payment_details if x.is_void != True]
        if len(active_payments) > 0:
            return True
        
        return False
    
    @property
    def payment_methods(self) -> str | None:
        methods:str = ""
        if len(self.payment_details) > 0:
            for pay in self.payment_details:
                methods += f'{pay.payment.payment_method.value}, ' 
            
            methods = methods[0:-2]
        
        return methods
    
    @property
    def utj_amount(self) -> Decimal | None:
        utj = 0
        if self.use_utj:
            utj = self.bidang.utj_amount
            # utj_current = next((invoice_utj for invoice_utj in self.bidang.invoices 
            #                     if (invoice_utj.jenis_bayar == JenisBayarEnum.UTJ or invoice_utj.jenis_bayar == JenisBayarEnum.UTJ_KHUSUS) 
            #                     and invoice_utj.is_void != True), None)
            
            # if utj_current:
            #     amount_payment_details = [payment_detail.amount for payment_detail in utj_current.payment_details if payment_detail.is_void != True]
            #     utj = sum(amount_payment_details) or 0
        
        return Decimal(utj)


class InvoiceDetailBase(SQLModel):
    invoice_id:Optional[UUID] = Field(foreign_key="invoice.id")
    bidang_komponen_biaya_id:Optional[UUID] = Field(foreign_key="bidang_komponen_biaya.id")
    # amount:Optional[condecimal(decimal_places=2)] = Field(nullable=True)

class InvoiceDetailFullBase(BaseUUIDModel, InvoiceDetailBase):
    pass

class InvoiceDetail(InvoiceDetailFullBase, table=True):
    invoice:"Invoice" = Relationship(
        back_populates="details",
        sa_relationship_kwargs=
        {
            "lazy":"select"
        }
    )

    bidang_komponen_biaya:"BidangKomponenBiaya" = Relationship(
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    @property
    def beban_pembeli(self) -> bool | None:
        return getattr(getattr(self, 'bidang_komponen_biaya', None), 'beban_pembeli', None)
    
    @property
    def amount(self) -> Decimal|None:
        return getattr(getattr(self, 'bidang_komponen_biaya', None), 'amount_calculate', None)
    
    @property
    def amount_beban_penjual(self) -> Decimal | None:
        amount = 0
        if self.bidang_komponen_biaya.beban_pembeli == False and self.bidang_komponen_biaya.is_void != True:
            if self.bidang_komponen_biaya.satuan_bayar == SatuanBayarEnum.Percentage and self.bidang_komponen_biaya.satuan_harga == SatuanHargaEnum.PerMeter2:
                    amount = (self.bidang_komponen_biaya.amount or 0) * ((self.bidang_komponen_biaya.bidang.luas_bayar or self.bidang_komponen_biaya.bidang.luas_surat) * (self.bidang_komponen_biaya.bidang.harga_transaksi or 0)/100)
            elif self.bidang_komponen_biaya.satuan_bayar == SatuanBayarEnum.Amount and self.bidang_komponen_biaya.satuan_harga == SatuanHargaEnum.PerMeter2:
                amount = (self.bidang_komponen_biaya.amount or 0) * (self.bidang_komponen_biaya.bidang.luas_bayar or self.bidang_komponen_biaya.bidang.luas_surat)
            else:
                amount = self.bidang_komponen_biaya.amount or 0
        
        return round(amount, 0)