from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.project_model import Project

class SectionBase(SQLModel):
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=50)

class SectionFullBase(BaseUUIDModel, SectionBase):
    pass

class Section(SectionFullBase, table=True):
    projects: list["Project"] = Relationship(back_populates="section", sa_relationship_kwargs={'lazy':'selectin'})