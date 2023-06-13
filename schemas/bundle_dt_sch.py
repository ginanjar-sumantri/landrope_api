from models.bundle_model import BundleDt, BundleDtBase, BundleDtFullBase
from common.partial import optional
from sqlmodel import Field

class BundleDtCreateSch(BundleDtBase):
    pass

class BundleDtSch(BundleDtFullBase):
    dokumen_name:str | None = Field(alias="dokumen_name")

@optional
class BundleDtUpdateSch(BundleDtBase):
    pass