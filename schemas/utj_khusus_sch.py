from models.utj_khusus_model import UtjKhusus, UtjKhususBase, UtjKhususFullBase
from schemas.utj_khusus_detail_sch import UtjKhususDetailExtSch, UtjKhususDetailSch
from schemas.invoice_sch import InvoiceExtSch
from schemas.termin_sch import TerminByIdUtjKhususSch
from common.partial import optional
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID

class UtjKhususCreateSch(UtjKhususBase):
    details:list[UtjKhususDetailExtSch]|None

class UtjKhususSch(UtjKhususFullBase):
    kjb_hd_code:str|None = Field(alias="kjb_hd_code")
    kjb_hd_group:str|None = Field(alias="kjb_hd_group")
    utj_amount:Decimal|None = Field(alias="utj_amount")
    termin_code:str|None = Field(alias="termin_code")
    jumlah_alashak:int|None = Field(alias="jumlah_alashak")
    total:Decimal|None = Field(alias="total")
    updated_by_name:str|None = Field(alias="updated_by_name")

class UtjKhususByIdSch(UtjKhususFullBase):
    kjb_hd_code:str|None = Field(alias="kjb_hd_code")
    kjb_hd_group:str|None = Field(alias="kjb_hd_group")
    kjb_hd_mediator:str|None
    utj_amount:Decimal|None = Field(alias="utj_amount")
    termin_code:str|None = Field(alias="termin_code")
    desa_name:str|None
    luas_kjb:Decimal|None
    details:list[UtjKhususDetailSch] | None

class UtjKhususPrintOutSch(SQLModel):
    desa_name:str|None
    amountExt:str|None
    luas_suratExt:str|None
    mediator:str|None

@optional
class UtjKhususUpdateSch(UtjKhususBase):
    details:list[UtjKhususDetailExtSch]|None