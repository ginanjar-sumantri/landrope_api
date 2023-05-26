from models.dokumen_model import BundleDt, BundleDtBase, BundleDtFullBase
from common.partial import optional

class BundleDtCreateSch(BundleDtBase):
    pass

class BundleDtSch(BundleDtFullBase):
    pass

@optional
class BundleDtUpdateSch(BundleDtBase):
    pass