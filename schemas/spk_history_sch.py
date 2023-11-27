from models.spk_model import SpkHistoryBase, SpkHistoryFullBase
from common.partial import optional
from sqlmodel import Field, SQLModel
from uuid import UUID


class SpkHistoryCreateSch(SpkHistoryBase):
    pass

class SpkHistorySch(SpkHistoryFullBase):
    trans_worker_name:str|None = Field(alias="trans_worker_name")