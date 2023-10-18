from models.termin_model import Termin, TerminBase, TerminFullBase
from schemas.invoice_sch import InvoiceExtSch, InvoiceSch
from schemas.termin_bayar_sch import TerminBayarExtSch, TerminBayarSch
from common.partial import optional
from common.enum import JenisBayarEnum, SatuanBayarEnum
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date

class TerminCreateSch(TerminBase):
    termin_bayars:list[TerminBayarExtSch]
    invoices:list[InvoiceExtSch]

class TerminSch(TerminFullBase):
    nomor_tahap:Optional[int] = Field(alias="nomor_tahap")
    kjb_hd_code:Optional[str] = Field(alias="kjb_hd_code")
    total_amount:Optional[Decimal] = Field(alias="total_amount")
    updated_by_name:str|None = Field(alias="updated_by_name")
    notaris_name:str|None = Field(alias="notaris_name")
    manager_name:str|None = Field(alias="manager_name")
    sales_name:str|None = Field(alias="sales_name")

class TerminByIdSch(TerminFullBase):
    nomor_tahap:Optional[int] = Field(alias="nomor_tahap")
    project_id:Optional[UUID] = Field(alias="project_id")
    project_name:Optional[str] = Field(alias="project_name")
    ptsk_id:Optional[UUID] = Field(alias="ptsk_id")
    ptsk_name:Optional[str] = Field(alias="ptsk_name")
    kjb_hd_code:Optional[str] = Field(alias="kjb_hd_code")
    utj_amount:Optional[Decimal] = Field(alias="utj_amount")
    notaris_name:str|None = Field(alias="notaris_name")
    manager_name:str|None = Field(alias="manager_name")
    sales_name:str|None = Field(alias="sales_name")
    termin_bayars:list[TerminBayarSch]
    invoices:list[InvoiceSch]

@optional
class TerminUpdateSch(TerminBase):
    termin_bayars:list[TerminBayarExtSch]
    invoices:list[InvoiceExtSch]

class TerminByIdForPrintOut(SQLModel):
    id:Optional[UUID]
    code:Optional[str]
    tahap_id:Optional[str]
    created_at:Optional[datetime]
    nomor_tahap:Optional[int]
    amount:Optional[Decimal]
    project_name:Optional[str]
    tanggal_transaksi:Optional[date]
    jenis_bayar:Optional[str]
    notaris_name:str|None 
    manager_name:str|None 
    sales_name:str|None 
    mediator:str|None
    remark:str|None

class TerminInvoiceforPrintOut(SQLModel):
    id_bidang:Optional[UUID]
    bidang_id:Optional[UUID]
    amount:Optional[Decimal]

class TerminInvoiceHistoryforPrintOut(SQLModel):
    id_bidang:Optional[str]
    jenis_bayar:Optional[JenisBayarEnum]
    str_jenis_bayar:Optional[str]
    tanggal_transaksi:Optional[date]
    amount:Optional[Decimal]

class TerminInvoiceHistoryforPrintOutExt(TerminInvoiceHistoryforPrintOut):
    amountExt:Optional[str]

class TerminUtjHistoryForPrintOut(SQLModel):
    id_bidang:Optional[str]
    jenis_bayar:Optional[JenisBayarEnum]
    amount:Optional[Decimal]

class TerminHistoryForPrintOut(SQLModel):
    id:UUID
    jenis_bayar:Optional[JenisBayarEnum]
    amount:Optional[Decimal]

class TerminBebanBiayaForPrintOut(SQLModel):
    id_bidang:Optional[str]
    beban_biaya_name:Optional[str]
    tanggungan:Optional[str]
    amount:Optional[Decimal]

class TerminBebanBiayaForPrintOutExt(TerminBebanBiayaForPrintOut):
    amountExt:Optional[str]

class BidangIDOfTerminSch(SQLModel):
    bidang_id:UUID

class TerminBidangIDSch(SQLModel):
    bidangs:list[BidangIDOfTerminSch]

