from models.project_model import ProjectBase, ProjectFullBase
from typing import TYPE_CHECKING, Optional
from common.partial import optional
from schemas.section_sch import SectionSch
from uuid import UUID
from sqlmodel import SQLModel, Field

class ProjectCreateSch(ProjectBase):
    pass

class ProjectSch(ProjectFullBase):
    section: Optional[SectionSch] = None
    main_project_code:str|None = Field(alias="main_project_code")

@optional
class ProjectUpdateSch(ProjectBase):
    pass

class ProjectForTreeReportSch(SQLModel):
    id:UUID|None
    name:str|None