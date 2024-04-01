from models.invoice_model import InvoiceBayar, InvoiceBayarBase, InvoiceBayarFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal

class InvoiceBayarCreateSch(InvoiceBayarBase):
    pass

class InvoiceBayarExtSch(SQLModel):
    id: UUID | None
    id_index: UUID | None
    amount: Decimal | None

class InvoiceBayarSch(InvoiceBayarFullBase):
    pass

@optional
class InvoiceBayarlUpdateSch(InvoiceBayarBase):
    pass