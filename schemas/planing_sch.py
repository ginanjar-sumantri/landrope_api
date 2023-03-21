from models.planing_model import PlaningBase, PlaningFullBase, PlaningRawBase
from common.partial import optional

class PlaningCreateSch(PlaningFullBase):
    pass

class PlaningSch(PlaningRawBase):
    pass

@optional
class PlaningUpdateSch(PlaningBase):
    pass