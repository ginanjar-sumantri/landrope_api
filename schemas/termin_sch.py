from models.termin_model import Termin, TerminBase, TerminFullBase
from schemas.invoice_sch import InvoiceExtSch, InvoiceSch, InvoiceInTerminSch, InvoiceInTerminUtjKhususSch
from schemas.termin_bayar_sch import TerminBayarExtSch, TerminBayarSch
from common.partial import optional
from common.enum import JenisBayarEnum, SatuanBayarEnum
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date

class TerminCreateSch(TerminBase):
    termin_bayars:list[TerminBayarExtSch]|None
    invoices:list[InvoiceExtSch]|None

class TerminSch(TerminFullBase):
    nomor_tahap:Optional[int] = Field(alias="nomor_tahap")
    kjb_hd_code:Optional[str] = Field(alias="kjb_hd_code")
    kjb_hd_group:Optional[str] = Field(alias="kjb_hd_group")
    total_amount:Optional[Decimal] = Field(alias="total_amount")
    updated_by_name:str|None = Field(alias="updated_by_name")
    notaris_name:str|None = Field(alias="notaris_name")
    manager_name:str|None = Field(alias="manager_name")
    sales_name:str|None = Field(alias="sales_name")
    status_workflow:str|None
    step_name_workflow:str|None

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
    invoices:list[InvoiceInTerminSch]

class TerminByIdUtjKhususSch(TerminFullBase):
    invoices:list[InvoiceInTerminUtjKhususSch]

@optional
class TerminUpdateSch(TerminBase):
    termin_bayars:list[TerminBayarExtSch]|None
    invoices:list[InvoiceExtSch]|None
    file: str | None 

class TerminByIdForPrintOut(SQLModel):
    id:Optional[UUID]
    code:Optional[str]
    nomor_memo:Optional[str]
    tahap_id:Optional[UUID]
    created_at:Optional[datetime]
    nomor_tahap:Optional[int]
    amount:Optional[Decimal]
    project_name:Optional[str]
    desa_name:Optional[str]
    ptsk_name:Optional[str]
    tanggal_transaksi:Optional[date]
    tanggal_rencana_transaksi:Optional[date]
    jenis_bayar:Optional[JenisBayarEnum]
    jenis_bayar_ext:Optional[str]
    notaris_name:str|None 
    manager_name:str|None 
    sales_name:str|None 
    mediator:str|None
    remark:str|None

class TerminInvoiceforPrintOut(SQLModel):
    id_bidang:Optional[UUID]
    bidang_id:Optional[UUID]
    amount:Optional[Decimal]

class TerminUtjHistoryForPrintOut(SQLModel):
    id_bidang:Optional[str]
    jenis_bayar:Optional[JenisBayarEnum]
    amount:Optional[Decimal]

class TerminHistoryForPrintOut(SQLModel):
    id:UUID
    jenis_bayar:Optional[JenisBayarEnum]
    amount:Optional[Decimal]

class TerminBebanBiayaForPrintOut(SQLModel):
    # id_bidang:Optional[str]
    beban_biaya_name:Optional[str]
    beban_pembeli:Optional[bool]
    is_void:Optional[bool]
    tanggungan:Optional[str]
    amount:Optional[Decimal]
    amountExt:Optional[str]
    

class BidangIDOfTerminSch(SQLModel):
    bidang_id:UUID

class TerminBidangIDSch(SQLModel):
    bidangs:list[BidangIDOfTerminSch]
    manager_id:UUID | None

class TerminIdSch(SQLModel):
    termin_ids:list[UUID]|None

class TerminExcelSch(SQLModel):
    id_bidang:str|None
    jenis_bayar:str|None
    percentage:str|None
    amount:str|None

class TerminVoidSch(SQLModel):
    void_reason:str

class TerminHistoriesSch(SQLModel):
    id:UUID|None
    tanggal_transaksi:date|None
    str_tanggal_transaksi:str|None
    jenis_bayar:JenisBayarEnum|None
    str_jenis_bayar:str|None
    amount:Decimal|None
    str_amount:str|None
    index_bidang:str|None
    beban_biayas:list[TerminBebanBiayaForPrintOut]|None

