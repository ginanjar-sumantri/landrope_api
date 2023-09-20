from models.invoice_model import InvoiceDetail, InvoiceDetailBase, InvoiceDetailFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field

class InvoiceDetailCreateSch(InvoiceDetailBase):
    pass

class InvoiceDetailSch(InvoiceDetailFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

@optional
class InvoiceDetailUpdateSch(InvoiceDetailSch):
    pass