from models.master_model import BebanBiaya
from common.partial import optional
from pydantic import BaseModel
from sqlmodel import Field

class BebanBiayaCreateSch(BaseModel):
    name:str
    is_active:bool

class BebanBiayaSch(BebanBiaya):
    updated_by_name2:str|None = Field(alias="updated_by_name")

@optional
class BebanBiayaUpdateSch(BaseModel):
    name:str
    is_active:bool