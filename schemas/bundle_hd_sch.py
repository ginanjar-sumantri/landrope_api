from models.bundle_model import BundleHd, BundleHdBase, BundleHdFullBase, BundleDt
from common.partial import optional
from sqlmodel import Field
from typing import List
from uuid import UUID

class BundleHdCreateSch(BundleHdBase):
    pass

class BundleHdSch(BundleHdFullBase):
    planing:str|None = Field(alias="planing_name")
    project:str|None = Field(alias="project_name")
    desa:str|None = Field(alias="desa_name")
    alashak:str|None = Field(alias="alashak")
    idbidang:str|None = Field(alias="idbidang")
    updated_by_name:str|None = Field(alias="updated_by_name")
    kjb_hd_code: str | None

class BundleHdByIdSch(BundleHdFullBase):
    planing:str|None = Field(alias="planing_name")
    project:str|None = Field(alias="project_name")
    desa:str|None = Field(alias="desa_name")
    alashak:str|None = Field(alias="alashak")
    idbidang:str|None = Field(alias="idbidang")
    updated_by_name:str|None = Field(alias="updated_by_name")
    kjb_hd_code: str | None

@optional
class BundleHdUpdateSch(BundleHdBase):
    pass