from models.master_model import BebanBiaya, BebanBiayaBase, BebanBiayaFullBase
from common.partial import optional
from pydantic import BaseModel
from sqlmodel import Field, SQLModel
from uuid import UUID

class BebanBiayaCreateSch(BebanBiayaBase):
    pass

class BebanBiayaSch(BebanBiayaFullBase):
    updated_by_name2:str|None = Field(alias="updated_by_name")


class BebanBiayaForSpkSch(SQLModel):
    beban_biaya_id:UUID|None
    beban_pembeli:bool|None
    beban_biaya_name:str|None
    is_tax:bool|None
    is_void:bool|None = Field(default=False)


@optional
class BebanBiayaUpdateSch(BebanBiayaBase):
    pass
