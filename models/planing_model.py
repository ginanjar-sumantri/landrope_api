from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import MappingPlaningPtsk
from uuid import UUID
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from models.ptsk_model import Ptsk
    from models.rincik_model import Rincik
    from models.bidang_model import Bidang

class PlaningBase(BaseGeoModel):
    project_id: UUID = Field(default=None, foreign_key="project.id")
    desa_id:UUID = Field(default=None, foreign_key="desa.id")
    luas:Decimal
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=50)

class PlaningFullBase(BaseUUIDModel, PlaningBase):
    pass

class Planing(PlaningFullBase, table=True):
    ptsks: list["Ptsk"] = Relationship(back_populates="planings", link_model=MappingPlaningPtsk)
    rinciks: list["Rincik"] = Relationship(back_populates="planing")
    bidangs: list["Bidang"] = Relationship(back_populates="planing")