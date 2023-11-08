from models.skpt_model import SkptDtBase, SkptDtFullBase, SkptDtRawBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field
from decimal import Decimal

@as_form
class SkptDtCreateSch(SkptDtBase):
    pass

class SkptDtRawSch(SkptDtRawBase):
    nomor_sk:str | None = Field(alias="nomor_sk")
    project_name:str | None = Field(alias="project_name")
    desa_name:str | None = Field(alias="desa_name")
    kota:str | None = Field(alias="kota")
    kecamatan:str | None = Field(alias="kecamatan")

class SkptDtSch(SkptDtFullBase):
    pass

@as_form
@optional
class SkptDtUpdateSch(SkptDtBase):
    pass