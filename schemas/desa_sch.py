from models.desa_model import DesaBase, DesaRawBase, DesaFullBase
from common.partial import optional
from common.as_form import as_form

@as_form
class DesaCreateSch(DesaBase):
    pass

class DesaRawSch(DesaRawBase):
    pass

class DesaSch(DesaFullBase):
    pass

@as_form
@optional
class DesaUpdateSch(DesaBase):
    pass