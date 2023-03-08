from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.section_model import Section
    from models.planing_model import Planing

class ProjectBase(SQLModel):
    section_id: UUID = Field(default=None, foreign_key="section.id")
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=50)

class ProjectFullBase(BaseUUIDModel, ProjectBase):
    pass

class Project(ProjectFullBase, table=True):
    section: "Section" = Relationship(back_populates="projects")
    planings: list["Planing"] = Relationship(back_populates="project")
