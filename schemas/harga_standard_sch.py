from models.master_model import HargaStandard, HargaStandardBase, HargaStandardFullBase
from common.partial import optional
from sqlmodel import Field, SQLModel
from common.enum import JenisAlashakEnum
from decimal import Decimal

class HargaStandardCreateSch(HargaStandardBase):
    pass

class HargaStandardSch(HargaStandardFullBase):
    planing_name:str|None = Field(alias="planing_name")
    updated_by_name:str|None = Field(alias="updated_by_name")

class HargaStandardKjbSch(SQLModel):
    jenis_alashak:JenisAlashakEnum|None
    harga:Decimal|None

@optional
class HargaStandardUpdateSch(HargaStandardBase):
    pass