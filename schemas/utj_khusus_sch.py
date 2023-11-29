from models.utj_khusus_model import UtjKhusus, UtjKhususBase, UtjKhususFullBase
from common.partial import optional
from sqlmodel import SQLModel, Field
from decimal import Decimal
from uuid import UUID

class UtjKhususCreateSch(UtjKhususBase):
    pass

class UtjKhususSch(UtjKhususFullBase):
    kjb_hd_code:str|None = Field(alias="kjb_hd_code")
    updated_by_name:str|None = Field(alias="updated_by_name")


class UtjKhususByIdSch(UtjKhususFullBase):
    kjb_hd_code:str|None = Field(alias="kjb_hd_code")

@optional
class UtjKhususUpdateSch(UtjKhususBase):
    pass