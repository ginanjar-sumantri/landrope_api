from models.rincik_model import RincikBase, RincikFullBase
from common.partial import optional

class RincikCreateSch(RincikBase):
    pass

class RincikSch(RincikFullBase):
    pass

@optional
class RincikUpdateSch(RincikBase):
    pass