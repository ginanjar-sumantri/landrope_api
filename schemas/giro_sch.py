from models.giro_model import GiroBase, GiroFullBase
from common.partial import optional
from decimal import Decimal
from sqlmodel import Field


class GiroCreateSch(GiroBase):
    pass

class GiroSch(GiroFullBase):
    is_used:bool|None = Field(alias="is_used")
    payment_code:str|None = Field(alias="payment_code")

@optional
class GiroUpdateSch(GiroFullBase):
    pass