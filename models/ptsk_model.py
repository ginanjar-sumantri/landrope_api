from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from enum import Enum
from datetime import date
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from models.skpt_model import Skpt
    # from models.rincik_model import Rincik
    # from models.bidang_model import Bidang, Bidangoverlap

class PtskBase(SQLModel):
    name:str = Field(nullable=False, max_length=100)
    code:str | None  = Field(nullable=True, max_length=50)

class PtskRawBase(BaseUUIDModel, PtskBase):
    pass

class PtskFullBase(PtskRawBase):
    pass

class Ptsk(PtskFullBase, table=True):
    skpts: list["Skpt"] = Relationship(back_populates="ptsk", sa_relationship_kwargs={'lazy':'selectin'})

