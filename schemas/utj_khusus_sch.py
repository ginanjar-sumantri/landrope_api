from models.utj_khusus_model import UtjKhusus, UtjKhususBase, UtjKhususFullBase
from schemas.invoice_sch import InvoiceExtSch
from schemas.termin_sch import TerminByIdUtjKhususSch
from common.partial import optional
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID

class UtjKhususCreateSch(UtjKhususBase):
    invoices:list[InvoiceExtSch]

class UtjKhususSch(UtjKhususFullBase):
    kjb_hd_code:str|None = Field(alias="kjb_hd_code")
    utj_amount:str|None = Field(alias="utj_amount")
    termin_code:str|None = Field(alias="termin_code")
    updated_by_name:str|None = Field(alias="updated_by_name")

class UtjKhususByIdSch(UtjKhususFullBase):
    kjb_hd_code:str|None = Field(alias="kjb_hd_code")
    utj_amount:str|None = Field(alias="utj_amount")
    termin_code:str|None = Field(alias="termin_code")
    termin:TerminByIdUtjKhususSch | None

@optional
class UtjKhususUpdateSch(UtjKhususBase):
    invoices:list[InvoiceExtSch]