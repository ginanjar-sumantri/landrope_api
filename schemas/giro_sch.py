from models.giro_model import GiroBase, GiroFullBase
from common.partial import optional
from decimal import Decimal
from sqlmodel import Field


class GiroCreateSch(GiroBase):
    pass

class GiroSch(GiroFullBase):
    giro_outstanding:Decimal|None = Field(alias="giro_outstanding")
    is_used:bool|None = Field(alias="is_used")
    giro_used:Decimal|None = Field(alias="giro_used")

@optional
class GiroUpdateSch(GiroFullBase):
    pass