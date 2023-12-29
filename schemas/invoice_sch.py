from models.invoice_model import Invoice, InvoiceBase, InvoiceFullBase
from schemas.invoice_detail_sch import InvoiceDetailExtSch, InvoiceDetailSch
from schemas.payment_detail_sch import PaymentDetailSch
from schemas.bidang_overlap_sch import BidangOverlapForPrintout
from common.partial import optional
from common.enum import JenisBayarEnum, JenisBidangEnum, SatuanBayarEnum
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID
from typing import Optional
from datetime import date

class InvoiceCreateSch(InvoiceBase):
    pass

class InvoiceExtSch(SQLModel):
    id:Optional[UUID]
    spk_id:Optional[UUID]
    bidang_id:Optional[UUID]
    amount:Optional[Decimal]
    use_utj:Optional[bool]
    details:list[InvoiceDetailExtSch]|None

class InvoiceSch(InvoiceFullBase):
    id_bidang:str|None = Field(alias="id_bidang")
    group:str|None = Field(alias="group")
    alashak:str|None = Field(alias="alashak")
    ptsk_name:str|None = Field(alias="ptsk_name")
    planing_name:str|None = Field(alias="planing_name")
    jenis_bayar:Optional[JenisBayarEnum] = Field(alias="jenis_bayar")
    nomor_tahap:Optional[int] = Field(alias="nomor_tahap")
    nomor_memo:Optional[str] = Field(alias="nomor_memo")
    code_termin:Optional[str] = Field(alias="code_termin")
    invoice_outstanding:Optional[Decimal] = Field(alias="invoice_outstanding")
    spk_amount:Optional[Decimal] = Field(alias="spk_amount")
    has_payment:Optional[bool] = Field(alias="has_payment")
    amount_nett:Optional[Decimal] = Field(alias="amount_nett")

    step_name_workflow:Optional[str] = Field(alias="step_name_workflow")
    status_workflow:Optional[str] = Field(alias="status_workflow")

    # payment_methods:Optional[str] = Field(alias="payment_methods")

    payment_details:list[PaymentDetailSch]|None
    details:list[InvoiceDetailSch]|None
    updated_by_name:str|None = Field(alias="updated_by_name")

class InvoiceInTerminSch(InvoiceSch):
    spk_code:Optional[str] = Field(alias="spk_code")
    luas_bayar:Optional[Decimal] = Field(alias="luas_bayar")
    harga_transaksi:Optional[Decimal] = Field(alias="harga_transaksi")
    invoice_outstanding:Optional[Decimal] = Field(alias="invoice_outstanding")
    utj_amount:Optional[Decimal] = Field(alias="utj_amount")

class InvoiceInTerminUtjKhususSch(InvoiceFullBase):
    pass

class InvoiceByIdSch(InvoiceFullBase):
    id_bidang:str|None = Field(alias="id_bidang")
    alashak:str|None = Field(alias="alashak")
    ptsk_name:str|None = Field(alias="ptsk_name")
    planing_name:str|None = Field(alias="planing_name")
    jenis_bayar:Optional[JenisBayarEnum] = Field(alias="jenis_bayar")
    nomor_tahap:Optional[int] = Field(alias="nomor_tahap")
    nomor_memo:Optional[str] = Field(alias="nomor_memo")
    code_termin:Optional[str] = Field(alias="code_termin")
    invoice_outstanding:Optional[Decimal] = Field(alias="invoice_outstanding")
    amount_nett:Optional[Decimal] = Field(alias="amount_nett")

    payment_details:list[PaymentDetailSch]
    details:list[InvoiceDetailSch]
    updated_by_name:str|None = Field(alias="updated_by_name")

class InvoiceByIdVoidSch(InvoiceFullBase):
    pass

class InvoiceSearchSch(InvoiceFullBase):
    id_bidang:str|None = Field(alias="id_bidang")
    alashak:str|None = Field(alias="alashak")
    jenis_bayar:Optional[JenisBayarEnum] = Field(alias="jenis_bayar")
    nomor_tahap:Optional[int] = Field(alias="nomor_tahap")
    nomor_memo:Optional[str] = Field(alias="nomor_memo")
    code_termin:Optional[str] = Field(alias="code_termin")
    invoice_outstanding:Optional[Decimal] = Field(alias="invoice_outstanding")
    amount_nett:Optional[Decimal] = Field(alias="amount_nett")
    
class InvoiceHistoryInTermin(InvoiceFullBase):
    id_bidang:str|None = Field(alias="id_bidang")
    alashak:str|None = Field(alias="alashak")
    nomor_memo:Optional[str] = Field(alias="nomor_memo")
    jenis_bayar:Optional[JenisBayarEnum] = Field(alias="jenis_bayar")
    spk_code:Optional[str] = Field(alias="spk_code")
    spk_satuan_bayar:SatuanBayarEnum | None = Field(alias="spk_satuan_bayar")
    amount_of_spk:Optional[Decimal] = Field(alias="amount_of_spk")
    amount_nett:Optional[Decimal] = Field(alias="amount_nett")
    amount_beban:Optional[Decimal] = Field(alias="amount_beban")
    utj_amount:Optional[Decimal] = Field(alias="utj_amount")
    invoice_outstanding:Optional[Decimal] = Field(alias="invoice_outstanding")
    has_payment:Optional[bool] = Field(alias="has_payment")
    

@optional
class InvoiceUpdateSch(InvoiceBase):
    pass

class InvoiceForPrintOutUtj(SQLModel):
    no:Optional[int]
    bidang_id:Optional[UUID]
    pemilik_name:Optional[str]
    mediator:Optional[str]
    alashak:Optional[str]
    luas_surat:Optional[Decimal]
    luas_suratExt:Optional[str]
    id_bidang:Optional[str]
    keterangan:Optional[str]
    desa_name:Optional[str]
    no_peta:Optional[str]
    project_name:Optional[str]
    ptsk_name:Optional[str]
    amount:Optional[Decimal]
    amountExt:Optional[str]

class InvoiceForPrintOut(SQLModel):
    id:Optional[UUID]
    bidang_id:Optional[UUID]
    id_bidang:Optional[str]
    group:Optional[str]
    jenis_bidang:Optional[JenisBidangEnum]
    lokasi:Optional[str]
    ptsk_name:Optional[str]
    status_il:Optional[str]
    project_name:Optional[str]
    desa_name:Optional[str]
    pemilik_name:Optional[str]
    alashak:Optional[str]
    luas_surat:Optional[Decimal]
    luas_ukur:Optional[Decimal]
    luas_gu_perorangan:Optional[Decimal]
    luas_nett:Optional[Decimal]
    luas_pbt_perorangan:Optional[Decimal]
    luas_bayar:Optional[Decimal]
    no_peta:Optional[str]
    harga_transaksi:Optional[Decimal]
    total_harga:Optional[Decimal]

    overlaps:Optional[list[BidangOverlapForPrintout]]

class InvoiceForPrintOutExt(InvoiceForPrintOut):
    no:Optional[int]
    harga_transaksiExt:Optional[str]
    total_hargaExt:Optional[str]
    luas_suratExt:Optional[str]
    luas_ukurExt:Optional[str]
    luas_gu_peroranganExt:Optional[str]
    luas_nettExt:Optional[str]
    luas_pbt_peroranganExt:Optional[str]
    luas_bayarExt:Optional[str]

class InvoiceHistoryforPrintOut(SQLModel):
    id:UUID|None
    id_bidang:str|None 
    jenis_bayar:Optional[JenisBayarEnum]
    str_jenis_bayar:Optional[str]
    tanggal_transaksi:Optional[date]
    amount:Optional[Decimal]
    amountExt:Optional[Decimal]

class InvoiceVoidSch(SQLModel):
    void_reason:str

class InvoiceLuasBayarSch(SQLModel):
    id:UUID|None
    luas_bayar:Decimal|None = Field(default=0)
    
    

