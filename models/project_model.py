from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING
from models.planing_model import Planing

if TYPE_CHECKING:
    from models.section_model import Section
    from models.desa_model import Desa

class ProjectBase(SQLModel):
    section_id: UUID = Field(default=None, foreign_key="section.id")
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=50)

class ProjectFullBase(BaseUUIDModel, ProjectBase):
    pass

class Project(ProjectFullBase, table=True):
    section: "Section" = Relationship(back_populates="projects")
    desas: list["Desa"] = Relationship(back_populates="projects", link_model=Planing)
