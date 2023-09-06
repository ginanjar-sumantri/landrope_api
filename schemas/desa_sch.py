from models.desa_model import DesaBase, DesaRawBase, DesaFullBase
from common.partial import optional
from common.as_form import as_form
from models.base_model import BaseGeoModel
from uuid import UUID
from decimal import Decimal
from sqlmodel import Field, SQLModel

@as_form
class DesaCreateSch(DesaBase):
    pass

class DesaRawSch(DesaRawBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

class DesaSch(DesaFullBase):
    updated_by_name:str|None = Field(alias="updated_by_name")

class DesaExportSch(BaseGeoModel):
    name:str | None
    code:str | None
    kecamatan:str | None
    kota:str | None
    luas:Decimal


@as_form
@optional
class DesaUpdateSch(DesaBase):
    pass

class DesaForTreeReportSch(SQLModel):
    id:UUID|None
    name:str|None
    project_id:UUID|None
    project_name:str|None