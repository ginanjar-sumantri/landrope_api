from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel, BaseGeoModel
from models.planing_model import Planing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.project_model import Project
    
    

class DesaBase(BaseGeoModel):
    name:str = Field(nullable=False, max_length=100)
    luas:int

class DesaFullBase(BaseUUIDModel, DesaBase):
    pass

class Desa(DesaFullBase, table=True):
    projects:list["Project"] = Relationship(back_populates="desas", link_model=Planing)

