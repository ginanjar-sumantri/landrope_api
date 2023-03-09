from models.desa_model import DesaBase, DesaFullBase
from common.partial import optional

class DesaCreateSch(DesaBase):
    pass

class DesaSch(DesaFullBase):
    pass

@optional
class DesaUpdateSch(DesaBase):
    pass