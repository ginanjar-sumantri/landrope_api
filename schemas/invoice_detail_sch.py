from models.invoice_model import InvoiceDetail, InvoiceDetailBase, InvoiceDetailFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal

class InvoiceDetailCreateSch(InvoiceDetailBase):
    pass

class InvoiceDetailExtSch(SQLModel):
    id:Optional[UUID]
    bidang_komponen_biaya_id:Optional[UUID]
    amount:Optional[Decimal]

class InvoiceDetailSch(InvoiceDetailFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")
    beban_pembeli:bool|None = Field(alias="beban_pembeli")

@optional
class InvoiceDetailUpdateSch(InvoiceDetailBase):
    pass