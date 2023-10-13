from models.invoice_model import Invoice, InvoiceBase, InvoiceFullBase
from schemas.invoice_detail_sch import InvoiceDetailExtSch, InvoiceDetailSch
from schemas.payment_detail_sch import PaymentDetailSch
from common.partial import optional
from common.enum import JenisBayarEnum
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID
from typing import Optional

class InvoiceCreateSch(InvoiceBase):
    pass

class InvoiceExtSch(SQLModel):
    id:Optional[UUID]
    spk_id:Optional[UUID]
    bidang_id:Optional[UUID]
    amount:Optional[Decimal]
    details:list[InvoiceDetailExtSch]

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

    payment_details:list[PaymentDetailSch]
    details:list[InvoiceDetailSch]
    updated_by_name:str|None = Field(alias="updated_by_name")

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

    payment_details:list[PaymentDetailSch]
    details:list[InvoiceDetailSch]
    updated_by_name:str|None = Field(alias="updated_by_name")

class InvoiceSearchSch(InvoiceFullBase):
    id_bidang:str|None = Field(alias="id_bidang")
    alashak:str|None = Field(alias="alashak")
    jenis_bayar:Optional[JenisBayarEnum] = Field(alias="jenis_bayar")
    nomor_tahap:Optional[int] = Field(alias="nomor_tahap")
    nomor_memo:Optional[str] = Field(alias="nomor_memo")
    code_termin:Optional[str] = Field(alias="code_termin")
    invoice_outstanding:Optional[Decimal] = Field(alias="invoice_outstanding")

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
    id_bidang:Optional[str]
    keterangan:Optional[str]
    desa_name:Optional[str]
    no_peta:Optional[str]
    project_name:Optional[str]
    ptsk_name:Optional[str]
    amount:Optional[Decimal]
    amountExt:Optional[str]

class InvoiceForPrintOut(SQLModel):
    bidang_id:Optional[UUID]
    id_bidang:Optional[str]
    group:Optional[str]
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

    #overlaps:Optional[list[]]

class InvoiceForPrintOutExt(InvoiceForPrintOut):
    no:Optional[int]
    harga_transaksiExt:Optional[str]
    total_hargaExt:Optional[str]
    luas_suratExt:Optional[str]
    luas_ukurExt:Optional[str]
    luas_nettExt:Optional[str]
    luas_bayarExt:Optional[str]

