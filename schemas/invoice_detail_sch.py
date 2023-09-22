from models.invoice_model import InvoiceDetail, InvoiceDetailBase, InvoiceDetailFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID

class InvoiceDetailCreateSch(InvoiceDetailBase):
    pass

class InvoiceDetailExtSch(SQLModel):
    id:Optional[UUID]
    komponen_id:Optional[UUID]

class InvoiceDetailSch(InvoiceDetailFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

@optional
class InvoiceDetailUpdateSch(InvoiceDetailSch):
    pass