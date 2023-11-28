from models.spk_model import SpkHistoryBase, SpkHistoryFullBase, SpkHistoryBaseExt
from common.partial import optional
from sqlmodel import Field, SQLModel
from uuid import UUID


class SpkHistoryCreateSch(SpkHistoryBaseExt):
    pass

class SpkHistorySch(SpkHistoryFullBase):
    trans_worker_name:str|None = Field(alias="trans_worker_name")