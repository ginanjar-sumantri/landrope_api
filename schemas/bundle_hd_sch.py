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

class BundleHdByIdSch(BundleHdSch):
    bundledts:list[BundleDt]

@optional
class BundleHdUpdateSch(BundleHdBase):
    pass