from models.invoice_model import Invoice, InvoiceBase, InvoiceFullBase
from common.partial import optional
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

class InvoiceSch(InvoiceFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

@optional
class InvoiceUpdateSch(InvoiceSch):
    pass