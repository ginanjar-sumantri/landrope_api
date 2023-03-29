from models.ptsk_model import PtskBase, PtskFullBase, PtskRawBase
from common.partial import optional
from common.as_form import as_form

@as_form
class PtskCreateSch(PtskBase):
    pass

class PtskRawSch(PtskRawBase):
    pass

class PtskSch(PtskFullBase):
    pass

@as_form
@optional
class PtskUpdateSch(PtskBase):
    pass