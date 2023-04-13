from models.draft_model import DraftBase, DraftRawBase, DraftFullBase
from common.as_form import as_form
from common.partial import optional

@as_form
class DraftCreateSch(DraftBase):
    pass

class DraftRawSch(DraftRawBase):
    pass

class DraftSch(DraftFullBase):
    pass

@as_form
@optional
class DraftUpdateSch(DraftBase):
    pass