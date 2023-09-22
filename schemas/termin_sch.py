from models.termin_model import Termin, TerminBase, TerminFullBase
from schemas.invoice_sch import InvoiceExtSch, InvoiceSch
from common.partial import optional
from sqlmodel import SQLModel, Field
from typing import Optional

class TerminCreateSch(TerminBase):
    invoices:list[InvoiceExtSch]

class TerminSch(TerminFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

class TerminByIdSch(TerminFullBase):
    nomor_tahap:Optional[str] = Field(alias="nomor_tahap")
    kjb_hd_code:Optional[str] = Field(alias="kjb_hd_code")
    invoices:list[InvoiceSch]

@optional
class TerminUpdateSch(TerminBase):
    invoices:list[InvoiceExtSch]