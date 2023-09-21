from models.master_model import BebanBiaya, BebanBiayaBase, BebanBiayaFullBase
from common.partial import optional
from pydantic import BaseModel
from sqlmodel import Field

class BebanBiayaCreateSch(BebanBiayaBase):
    pass

class BebanBiayaSch(BebanBiayaFullBase):
    updated_by_name2:str|None = Field(alias="updated_by_name")

@optional
class BebanBiayaUpdateSch(BebanBiayaBase):
    pass
