from models.planing_model import PlaningBase, PlaningFullBase, PlaningRawBase
from schemas.project_sch import ProjectSch
from schemas.desa_sch import DesaRawSch
from common.partial import optional
from common.as_form import as_form

@as_form
class PlaningCreateSch(PlaningBase):
    pass

class PlaningRawSch(PlaningRawBase):
    project:ProjectSch = None
    desa:DesaRawSch = None

class PlaningSch(PlaningFullBase):
    pass

@as_form
@optional
class PlaningUpdateSch(PlaningBase):
    pass