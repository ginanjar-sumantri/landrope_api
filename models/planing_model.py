from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.mapping_model import (Mapping_Planing_Ptsk, Mapping_Planing_Ptsk_Desa, 
                                      Mapping_Planing_Ptsk_Desa_Rincik, Mapping_Planing_Ptsk_Desa_Rincik_Bidang)
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.project_model import Project
    from models.ptsk_model import Ptsk
    from models.desa_model import Desa
    from models.rincik_model import Rincik
    from models.bidang_model import Bidang

class PlaningBase(BaseGeoModel):
    project_id: UUID = Field(default=None, foreign_key="project.id")
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=50)

class PlaningFullBase(BaseUUIDModel, PlaningBase):
    pass

class Planing(PlaningFullBase, table=True):
    project: "Project" = Relationship(back_populates="planings")
    ptsks:list["Ptsk"] = Relationship(back_populates="planings", link_model=Mapping_Planing_Ptsk)
    desas:list["Desa"] = Relationship(back_populates="planings", link_model=Mapping_Planing_Ptsk_Desa)
    rinciks:list["Rincik"] = Relationship(back_populates="planing", link_model=Mapping_Planing_Ptsk_Desa_Rincik)
    bidangs:list["Bidang"] = Relationship(back_populates="planing", link_model=Mapping_Planing_Ptsk_Desa_Rincik_Bidang)

    