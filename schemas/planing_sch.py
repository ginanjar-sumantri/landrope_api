from models.planing_model import PlaningBase, PlaningFullBase
from common.partial import optional

class PlaningCreateSch(PlaningBase):
    pass

class PlaningSch(PlaningFullBase):
    pass

@optional
class PlaningUpdateSch(PlaningBase):
    pass