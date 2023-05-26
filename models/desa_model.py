from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.planing_model import Planing
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from models.planing_model import Planing
    
class DesaBase(SQLModel):
    name:str = Field(nullable=False, max_length=100)
    code:str | None = Field(nullable=True, max_length=50)
    kecamatan:str | None = Field(nullable=True, max_length=100)
    kota:str | None = Field(nullable=True, max_length=100)
    luas:Decimal
    last:int | None = Field(default=1, nullable=True) #untuk mengetahui nomor terakhir id bidang di desa tsb
    digit:int | None = Field(default=4, nullable=True) #digit untuk id bidang di desa tsb

class DesaRawBase(BaseUUIDModel, DesaBase):
    pass

class DesaFullBase(DesaRawBase, BaseGeoModel):
    pass

class Desa(DesaFullBase, table=True):
    desa_planings:list["Planing"] = Relationship(back_populates="desa", sa_relationship_kwargs={'lazy':'selectin'})

