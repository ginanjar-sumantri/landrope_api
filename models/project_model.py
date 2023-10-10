from sqlmodel import SQLModel, Field, Relationship
from models.base_model import BaseUUIDModel
from uuid import UUID
from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from models.planing_model import Planing
    from models.section_model import Section
    

class ProjectBase(SQLModel):
    section_id: UUID = Field(default=None, foreign_key="section.id", nullable=True)
    name:str = Field(nullable=False, max_length=100)
    code:str = Field(nullable=False, max_length=50)
    main_project_id:Optional[UUID] = Field(nullable=True, foreign_key="main_project.id")

class ProjectFullBase(BaseUUIDModel, ProjectBase):
    pass

class Project(ProjectFullBase, table=True):
    section: "Section" = Relationship(back_populates="projects", sa_relationship_kwargs={'lazy':'select'})
    project_planings: list["Planing"] = Relationship(back_populates="project", sa_relationship_kwargs={'lazy':'select'})
    main_project:"MainProject" = Relationship(sa_relationship_kwargs={'lazy':'select'})
    sub_projects:list["SubProject"] = Relationship(back_populates="project", sa_relationship_kwargs={'lazy':'select', 'viewonly':True})

    @property
    def sub_project_exists(self) -> bool | None:
        if len(self.sub_projects) > 0:
            return True
        
        return False
    
    @property
    def main_project_code(self) -> str|None:
        return getattr(getattr(self, 'main_project', None), 'code', None)


class SubProjectBase(SQLModel):
    name:str = Field(nullable=False)
    code:str = Field(nullable=True)
    project_id:UUID = Field(foreign_key="project.id")
    main_project_id:UUID = Field(foreign_key="main_project.id")

class SubProjectFullBase(BaseUUIDModel, SubProjectBase):
    pass

class SubProject(SubProjectFullBase, table=True):
    project:"Project" = Relationship(
        back_populates="sub_projects",
        sa_relationship_kwargs=
        {
            'lazy' : 'select'
        }
    )

    main_project:"MainProject" = Relationship(
        sa_relationship_kwargs=
        {
            'lazy' : 'select'
        }
    )

    @property
    def project_name(self) -> str|None:
        return getattr(getattr(self, 'project', None), 'name', None)
    
    @property
    def last_tahap(self) -> int|None:
        return getattr(getattr(self, 'main_project', None), 'last_tahap', None)
    
    @property
    def main_project_code(self) -> str|None:
        return getattr(getattr(self, 'main_project', None), 'code', None)

class MainProjectBase(SQLModel):
    code:str
    last_tahap:Optional[int] = Field(nullable=True)

class MainProjectFullBase(BaseUUIDModel, MainProjectBase):
    pass

class MainProject(MainProjectFullBase, table=True):
    sub_projects:list["SubProject"] = Relationship(
        sa_relationship_kwargs=
        {
            'lazy' : 'select',
            'viewonly' : True
        }
    )

