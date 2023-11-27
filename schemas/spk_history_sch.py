from models.spk_model import SpkHistoryBase, SpkHistoryFullBase
from common.partial import optional
from sqlmodel import Field, SQLModel
from uuid import UUID


class SpkHistoryCreateSch(SpkHistoryBase):
    pass

class SpkHistorySch(SpkHistoryFullBase):
    pass