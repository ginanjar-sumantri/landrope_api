from models.desa_model import DesaBase, DesaRawBase, DesaFullBase
from common.partial import optional
from common.as_form import as_form
from models.base_model import BaseGeoModel
from uuid import UUID
from decimal import Decimal

@as_form
class DesaCreateSch(DesaBase):
    pass

class DesaRawSch(DesaRawBase):
    pass

class DesaSch(DesaFullBase):
    pass

class DesaExportSch(BaseGeoModel):
    id:UUID
    name:str | None
    code_desa:str | None
    kecamatan:str | None
    kota:str | None
    luas:Decimal


@as_form
@optional
class DesaUpdateSch(DesaBase):
    pass