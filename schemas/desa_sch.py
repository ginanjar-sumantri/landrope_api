from models.desa_model import DesaBase, DesaRawBase, DesaFullBase
from common.partial import optional

class DesaCreateSch(DesaFullBase):
    pass

class DesaSch(DesaRawBase):
    pass

@optional
class DesaUpdateSch(DesaBase):
    pass