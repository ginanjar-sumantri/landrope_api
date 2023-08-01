from models.bundle_model import BundleDt, BundleDtBase, BundleDtFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field

class BundleDtCreateSch(BundleDtBase):
    pass

class BundleDtSch(BundleDtFullBase):
    dokumen_name:str | None = Field(alias="dokumen_name")
    file_exists:bool | None = Field(alias="file_exists")

@as_form
@optional
class BundleDtUpdateSch(BundleDtBase):
    pass