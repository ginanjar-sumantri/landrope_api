from models.planing_model import PlaningBase, PlaningFullBase, PlaningRawBase
from schemas.project_sch import ProjectSch
from common.partial import optional

class PlaningCreateSch(PlaningBase):
    pass

class PlaningRawSch(PlaningRawBase):
    pass

class PlaningSch(PlaningFullBase):
    pass

@optional
class PlaningUpdateSch(PlaningBase):
    pass