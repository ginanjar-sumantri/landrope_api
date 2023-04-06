from models.planing_model import PlaningBase, PlaningFullBase, PlaningRawBase
from schemas.project_sch import ProjectSch
from schemas.desa_sch import DesaRawSch
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field

@as_form
class PlaningCreateSch(PlaningBase):
    pass

class PlaningRawSch(PlaningRawBase):
    project_name:str = Field(alias='project_name')
    desa_name:str = Field(alias='desa_name')
    section_name:str | None = Field(alias='section_name')

class PlaningSch(PlaningFullBase):
    pass

@as_form
@optional
class PlaningUpdateSch(PlaningBase):
    pass