from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import Mapping_Planing_Ptsk_Desa, Mapping_Planing_Ptsk_Desa_Rincik, Mapping_Planing_Ptsk_Desa_Rincik_Bidang
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.ptsk_model import Ptsk
    from models.rincik_model import Rincik
    from models.bidang_model import Bidang
    

class DesaBase(BaseGeoModel):
    name:str = Field(nullable=False, max_length=100)
    luas:int

class DesaFullBase(BaseUUIDModel, DesaBase):
    pass

class Desa(DesaFullBase, table=True):
    planings:list["Planing"] = Relationship(back_populates="desas", link_model=Mapping_Planing_Ptsk_Desa)
    ptsks:list["Ptsk"] = Relationship(back_populates="desas", link_model=Mapping_Planing_Ptsk_Desa)
    rinciks:list["Rincik"] = Relationship(back_populates="desa", link_model=Mapping_Planing_Ptsk_Desa_Rincik)
    bidangs:list["Bidang"] = Relationship(back_populates="desa", link_model=Mapping_Planing_Ptsk_Desa_Rincik_Bidang)

