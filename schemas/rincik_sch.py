from models.rincik_model import RincikBase, RincikFullBase, RincikRawBase
from common.partial import optional
from common.as_form import as_form

from sqlmodel import Field

@as_form
class RincikCreateSch(RincikBase):
    pass

class RincikRawSch(RincikRawBase):
    jenis_lahan_name:str | None = Field(alias='jenis_lahan_name')
    planing_name:str|None = Field(alias='planing_name')
    project_name:str|None = Field(alias='project_name')
    desa_name:str|None = Field(alias='desa_name')
    section_name:str|None = Field(alias='section_name')
    ptsk_name:str|None = Field(alias='ptsk_name')
    nomor_sk:str|None = Field(alias='nomor_sk')

class RincikSch(RincikFullBase):
    pass

@as_form
@optional
class RincikUpdateSch(RincikBase):
    pass