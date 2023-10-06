from models.planing_model import PlaningBase, PlaningFullBase, PlaningRawBase
from schemas.project_sch import ProjectSch
from schemas.desa_sch import DesaRawSch
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field
from models.base_model import BaseGeoModel
from decimal import Decimal
from uuid import UUID

@as_form
class PlaningCreateSch(PlaningBase):
    pass

class PlaningRawSch(PlaningRawBase):
    project_name:str = Field(alias='project_name')
    desa_name:str = Field(alias='desa_name')
    section_name:str | None = Field(alias='section_name')
    sub_project_exists:bool | None = Field(alias="sub_project_exists")

class PlaningSch(PlaningFullBase):
    pass

class PlaningExtSch(PlaningFullBase):
    project_name:str | None
    desa_name:str | None
    section_name:str | None

class PlaningShpSch(BaseGeoModel):
    name:str | None
    code:str | None
    project:str | None
    desa:str | None
    section:str | None
    luas:Decimal | None

@as_form
@optional
class PlaningUpdateSch(PlaningBase):
    pass