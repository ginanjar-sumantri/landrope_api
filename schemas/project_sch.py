from models.project_model import ProjectBase, ProjectFullBase
from typing import TYPE_CHECKING, Optional
from common.partial import optional
from common.as_form import as_form
from schemas.section_sch import SectionSch

class ProjectCreateSch(ProjectBase):
    pass

class ProjectSch(ProjectFullBase):
    section: Optional[SectionSch] = None


@optional
class ProjectUpdateSch(ProjectBase):
    pass