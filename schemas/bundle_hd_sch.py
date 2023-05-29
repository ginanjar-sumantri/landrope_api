from models.dokumen_model import BundleHd, BundleHdBase, BundleHdFullBase, BundleDt
from common.partial import optional
from sqlmodel import Field
from typing import List
from uuid import UUID

class BundleHdCreateSch(BundleHdBase):
    pass

class BundleHdSch(BundleHdFullBase):
    pass

class BundleHdByIdSch(BundleHdSch):
    bundledts:list[BundleDt]

@optional
class BundleHdUpdateSch(BundleHdBase):
    pass