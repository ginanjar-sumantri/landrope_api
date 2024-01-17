from models.kjb_model import KjbHistory, KjbHistoryFullBase, KjbHistoryBaseExt
from common.partial import optional
from sqlmodel import Field, SQLModel
from uuid import UUID


class KjbHistoryCreateSch(KjbHistoryBaseExt):
    pass

class KjbHistorySch(KjbHistoryFullBase):
    trans_worker_name:str|None = Field(alias="trans_worker_name")