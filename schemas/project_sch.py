from models.project_model import ProjectBase, ProjectFullBase
from common.partial import optional

class ProjectCreateSch(ProjectBase):
    pass

class ProjectSch(ProjectFullBase):
    pass

@optional
class ProjectUpdateSch(ProjectBase):
    pass