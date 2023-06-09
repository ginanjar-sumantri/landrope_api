from models.master_model import BebanBiaya
from common.partial import optional
from pydantic import BaseModel

class BebanBiayaCreateSch(BaseModel):
    name:str
    is_active:bool

class BebanBiayaSch(BebanBiaya):
    pass

@optional
class BebanBiayaUpdateSch(BaseModel):
    name:str
    is_active:bool