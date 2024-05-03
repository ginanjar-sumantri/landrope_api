from sqlmodel import SQLModel, Field
from models.base_model import BaseUUIDModel
from uuid import UUID

class TerminRfpPaymentBase(SQLModel):
    termin_id: UUID | None = Field(default=None, foreign_key="termin.id")
    rfp_id: UUID | None = Field(default=None)
    payment_id: UUID | None = Field(default=None, foreign_key="payment.id")
    status: str | None = Field(default=None) #status workflow rfp

class TerminRfpPaymentFullBase(BaseUUIDModel, TerminRfpPaymentBase):
    pass

class TerminRfpPayment(TerminRfpPaymentFullBase, table=True):
    pass