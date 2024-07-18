from sqlmodel import SQLModel, Field
from uuid import UUID
from datetime import date
from decimal import Decimal

class RfpLineNotificationSch(SQLModel):
    id: str | None = Field(alias='id')
    reff_no: str | None = Field(alias='reff_no')

class RfpBankNotificationSch(SQLModel):
    id: str | None = Field(alias='id')
    giro_no: str | None = Field(alias='giro_no')
    bank_code: str | None = Field(alias='bank_code')
    date_doc: date | None = Field(alias='date_doc')
    posting_date: date | None = Field(alias='posting_date')

class RfpAllocationNotificationSch(SQLModel):
    amount: Decimal | None = Field(alias='amount')
    rfp_bank_id: str | None = Field(alias='rfp_bank_id')
    rfp_line_id: str | None = Field(alias='rfp_line_id')


class RfpHeadNotificationSch(SQLModel):
    id: str | None = Field(alias='id')
    doc_no: str | None = Field(alias='doc_no')
    client_ref_no: str = Field(alias='client_ref_no')
    current_step: str | None = Field(alias='current_step')
    descs: str | None = Field(alias='descs')
    is_void: bool | None = Field(default=False, alias="is_void")
    void_reason: str | None = Field(default=None)
    void_date: date | None = Field(default=None)

    rfp_lines: list[RfpLineNotificationSch] | None
    rfp_banks: list[RfpBankNotificationSch] | None
    rfp_allocations: list[RfpAllocationNotificationSch] | None