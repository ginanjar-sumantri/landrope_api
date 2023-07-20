from models.ptsk_model import PtskBase, PtskFullBase, PtskRawBase
from common.partial import optional

class PtskCreateSch(PtskBase):
    pass

class PtskRawSch(PtskRawBase):
    pass

class PtskSch(PtskFullBase):
    pass

@optional
class PtskUpdateSch(PtskBase):
    pass