from models.project_model import ProjectBase, ProjectFullBase
from common.partial import optional
from common.as_form import as_form

@as_form
class ProjectCreateSch(ProjectBase):
    pass

class ProjectSch(ProjectFullBase):
    pass


@as_form
@optional
class ProjectUpdateSch(ProjectBase):
    pass