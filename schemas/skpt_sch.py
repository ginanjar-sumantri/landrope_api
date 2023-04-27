from models.skpt_model import SkptBase, SkptFullBase, SkptRawBase
from common.partial import optional
from common.as_form import as_form

@as_form
class SkptCreateSch(SkptBase):
    pass

class SkptRawSch(SkptRawBase):
    pass

class SkptSch(SkptFullBase):
    pass

@as_form
@optional
class SkptUpdateSch(SkptBase):
    pass