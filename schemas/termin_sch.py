from models.termin_model import Termin, TerminBase, TerminFullBase
from schemas.invoice_sch import InvoiceExtSch
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field

class TerminCreateSch(TerminBase):
    invoices:list[InvoiceExtSch]

class TerminSch(TerminFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

@optional
class TerminUpdateSch(TerminBase):
    pass