from models.termin_model import Termin, TerminBase, TerminFullBase
from schemas.invoice_sch import InvoiceExtSch, InvoiceSch
from common.partial import optional
from common.enum import JenisBayarEnum, SatuanBayarEnum
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

class TerminCreateSch(TerminBase):
    invoices:list[InvoiceExtSch]

class TerminSch(TerminFullBase):
    nomor_tahap:Optional[int] = Field(alias="nomor_tahap")
    kjb_hd_code:Optional[str] = Field(alias="kjb_hd_code")
    total_amount:Optional[Decimal] = Field(alias="total_amount")
    updated_by_name:str|None = Field(alias="updated_by_name")

class TerminByIdSch(TerminFullBase):
    nomor_tahap:Optional[int] = Field(alias="nomor_tahap")
    kjb_hd_code:Optional[str] = Field(alias="kjb_hd_code")
    utj_amount:Optional[Decimal] = Field(alias="utj_amount")
    invoices:list[InvoiceSch]

@optional
class TerminUpdateSch(TerminBase):
    invoices:list[InvoiceExtSch]

class TerminByIdForPrintOut(SQLModel):
    id:UUID
    code:Optional[str]
    tahap_id:Optional[str]
    created_at:Optional[datetime]
    nomor_tahap:Optional[int]
    amount:Optional[Decimal]
    project_name:Optional[str]

class TerminBidangForPrintOut(SQLModel):
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

class TerminBidangForPrintOutExt(TerminBidangForPrintOut):
    no:Optional[int]
    harga_transaksiExt:Optional[str]
    total_hargaExt:Optional[str]

class TerminInvoiceforPrintOut(SQLModel):
    invoice_id:Optional[UUID]
    bidang_id:Optional[UUID]
    amount:Optional[Decimal]

class TerminInvoiceHistoryforPrintOut(SQLModel):
    bidang_id:Optional[UUID]
    id_bidang:Optional[str]
    jenis_bayar:Optional[JenisBayarEnum]
    nilai:Optional[Decimal]
    satuan_bayar:Optional[SatuanBayarEnum]
    tanggal_bayar:Optional[datetime]
    amount:Optional[Decimal]

class TerminUtjHistoryForPrintOut(SQLModel):
    jenis_bayar:Optional[JenisBayarEnum]
    amount:Optional[Decimal]

class TerminHistoryForPrintOut(SQLModel):
    id:UUID
    jenis_bayar:Optional[JenisBayarEnum]
    amount:Optional[Decimal]

class TerminBebanBiayaForPrintOut(SQLModel):
    beban_biaya_name:Optional[str]
    tanggungan:Optional[str]
    amount:Optional[Decimal]

