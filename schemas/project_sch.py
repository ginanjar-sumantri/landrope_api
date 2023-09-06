from models.project_model import ProjectBase, ProjectFullBase
from typing import TYPE_CHECKING, Optional
from common.partial import optional
from schemas.section_sch import SectionSch
from uuid import UUID
from sqlmodel import SQLModel

class ProjectCreateSch(ProjectBase):
    pass

class ProjectSch(ProjectFullBase):
    section: Optional[SectionSch] = None

@optional
class ProjectUpdateSch(ProjectBase):
    pass

class ProjectForTreeReportSch(SQLModel):
    id:UUID|None
    name:str|None