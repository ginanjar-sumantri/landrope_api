from models.dokumen_model import BundleHd, BundleHdBase, BundleHdFullBase, BundleDt
from common.partial import optional
from sqlmodel import Field

class BundleHdCreateSch(BundleHdBase):
    pass

class BundleHdSch(BundleHdFullBase):
    bundling_code:str|None = Field(alias='get_bundling_code')
    bundle_dts:list[BundleDt]

@optional
class BundleHdUpdateSch(BundleHdBase):
    pass