from models.rincik_model import RincikBase, RincikFullBase, RincikRawBase
from common.partial import optional
from common.as_form import as_form

@as_form
class RincikCreateSch(RincikBase):
    pass

class RincikRawSch(RincikRawBase):
    pass

class RincikSch(RincikFullBase):
    pass

as_form
@optional
class RincikUpdateSch(RincikBase):
    pass