from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional
from common.enum import JenisBayarEnum, SatuanBayarEnum, SatuanHargaEnum, PaymentStatusEnum
from decimal import Decimal
from datetime import date, datetime
from pydantic import condecimal
import numpy

if TYPE_CHECKING:
    from models import Worker, Termin, Spk, Bidang, BidangKomponenBiaya, PaymentDetail, TerminBayar
    

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
    payment_status:Optional[PaymentStatusEnum] = Field(nullable=True)
    realisasi: bool | None = Field(nullable=True, default=False)

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

    bayars:list["InvoiceBayar"] = Relationship(
        back_populates="invoice",
        sa_relationship_kwargs=
        {
            "lazy" : "select",
            "cascade" : "delete, all",
             "foreign_keys" : "[InvoiceBayar.invoice_id]"
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
            "lazy": "joined",
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
    def id_bidang_lama(self) -> str | None:
        return getattr(getattr(self, "bidang", None), "id_bidang_lama", None)
    
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
        if self.is_void:
            return total_payment
        
        if len(self.payment_details) > 0:
            array_payment = [payment_dtl.amount for payment_dtl in self.payment_details if payment_dtl.is_void != True and payment_dtl.realisasi != True]
            total_payment = sum(array_payment)
        
        return Decimal(self.amount - Decimal(total_payment) - self.amount_beban - self.utj_amount)
    
    @property
    def amount_nett(self) -> Decimal | None:
        return Decimal(self.amount - self.amount_beban - self.utj_amount)
    
    @property
    def amount_beban(self) -> Decimal | None:
        beban_penjual = sum([dt.amount_beban_penjual for dt in self.details if dt.bidang_komponen_biaya.beban_pembeli ==  False])
        
        return beban_penjual
    
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

        return Decimal(utj)
    
    @property
    def utj_outstanding(self) -> Decimal | None:
        utj = 0
        if self.bidang.utj_has_use == False:
            utj = self.bidang.utj_amount

        return Decimal(utj)
    
    @property
    def spk_nilai(self) -> Decimal | None:
        return getattr(getattr(self, "spk", None), "amount", None)
    
    @property
    def satuan_bayar(self) -> SatuanBayarEnum | None:
        return getattr(getattr(self, "spk", None), "satuan_bayar", None)
    
    @property
    def last_payment_status_at(self) -> date | None:

        tgl_cair:date | None = None
        tgl_buka:date | None = None

        payment_dtl_1 = next((p_dt for p_dt in self.payment_details if p_dt.is_void != True), None)
        payment_dtl_2 = next((p_dt for p_dt in self.payment_details if p_dt.is_void != True and p_dt.giro_id is not None), None)

        if payment_dtl_2 is None and payment_dtl_1 is None:
            return None

        tgl_buka = payment_dtl_2.payment_giro.tanggal_buka if payment_dtl_2 else payment_dtl_1.payment.giro.tanggal_buka
        tgl_cair = payment_dtl_2.payment_giro.tanggal_cair if payment_dtl_2 else payment_dtl_1.payment.giro.tanggal_cair

        if tgl_cair:
            return tgl_cair
        elif tgl_buka:
            return tgl_buka
        else:
            return None
        
    @property
    def payment_status_ext(self) -> str | None:

        tgl_cair:date | None = None
        tgl_buka:date | None = None

        payment_dtl_1 = next((p_dt for p_dt in self.payment_details if p_dt.is_void != True), None)
        payment_dtl_2 = next((p_dt for p_dt in self.payment_details if p_dt.is_void != True and p_dt.giro_id is not None), None)

        if payment_dtl_2 is None and payment_dtl_1 is None:
            return None

        tgl_buka = payment_dtl_2.payment_giro.tanggal_buka if payment_dtl_2 else payment_dtl_1.payment.giro.tanggal_buka
        tgl_cair = payment_dtl_2.payment_giro.tanggal_cair if payment_dtl_2 else payment_dtl_1.payment.giro.tanggal_cair

        if tgl_cair:
            return "CAIR_GIRO"
        elif tgl_buka:
            return "BUKA_GIRO"
        else:
            return None
    
   
    
    @property
    def step_name_workflow(self) -> str | None:
        return getattr(getattr(self, "termin", None), "step_name_workflow", None)
    
    @property
    def status_workflow(self) -> str | None:
        return getattr(getattr(self, "termin", None), "status_workflow", None)
    
    @property
    def last_status_at(self) -> datetime | None:
        last_status:datetime | None = getattr(getattr(self, "termin", None), "last_status_at", None)

        if last_status:
            return last_status.date()
        
        return last_status


class InvoiceDetailBase(SQLModel):
    invoice_id:Optional[UUID] = Field(foreign_key="invoice.id")
    bidang_komponen_biaya_id:Optional[UUID] = Field(foreign_key="bidang_komponen_biaya.id")
    amount:Optional[Decimal] = Field(nullable=True)

class InvoiceDetailFullBase(BaseUUIDModel, InvoiceDetailBase):
    pass

class InvoiceDetail(InvoiceDetailFullBase, table=True):
    invoice:"Invoice" = Relationship(
        back_populates="details",
        sa_relationship_kwargs=
        {
            "lazy":"selectin"
        }
    )

    bidang_komponen_biaya:"BidangKomponenBiaya" = Relationship(
        back_populates="invoice_details",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    @property
    def beban_pembeli(self) -> bool | None:
        return getattr(getattr(self, 'bidang_komponen_biaya', None), 'beban_pembeli', None)
    
    @property
    def is_void(self) -> bool | None:
        return getattr(getattr(self, 'bidang_komponen_biaya', None), 'is_void', None)
    
    @property
    def amount_beban_penjual(self) -> Decimal | None:
        amount = 0
        if self.invoice.jenis_bayar != JenisBayarEnum.PENGEMBALIAN_BEBAN_PENJUAL:
            if self.bidang_komponen_biaya.beban_pembeli == False:
                amount = self.amount or 0
        
        return round(amount, 0)
    
    @property
    def beban_biaya_name(self) -> str | None:
        return getattr(getattr(self, 'bidang_komponen_biaya', None), 'beban_biaya_name', None)
    
    @property
    def beban_biaya_id(self) -> str | None:
        return getattr(getattr(self, 'bidang_komponen_biaya', None), 'beban_biaya_id', None)
    
    @property
    def satuan_harga(self) -> SatuanHargaEnum | None:
        return getattr(getattr(self, 'bidang_komponen_biaya', None), 'satuan_harga', None)
    
    @property
    def satuan_bayar(self) -> SatuanBayarEnum | None:
        return getattr(getattr(self, 'bidang_komponen_biaya', None), 'satuan_bayar', None)
    
    @property
    def komponen_biaya_amount(self) -> Decimal | None:
        return getattr(getattr(self, 'bidang_komponen_biaya', None), 'amount', None)


class InvoiceBayarBase(SQLModel):
    termin_bayar_id: UUID | None = Field(nullable=False, foreign_key="termin_bayar.id")
    invoice_id: UUID | None = Field(nullable=False, foreign_key="invoice.id")
    amount:Decimal | None = Field(nullable=True, default=0)

class InvoiceBayarFullBase(BaseUUIDModel, InvoiceBayarBase):
    pass

class InvoiceBayar(InvoiceBayarFullBase, table=True):
    termin_bayar:"TerminBayar" = Relationship(
        back_populates="invoice_bayars",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )

    invoice:"Invoice" = Relationship(
        back_populates="bayars",
        sa_relationship_kwargs=
        {
            "lazy" : "select"
        }
    )