from models.ptsk_model import PtskBase, PtskFullBase
from common.partial import optional

class PtskCreateSch(PtskBase):
    pass

class PtskSch(PtskFullBase):
    pass

@optional
class PtskUpdateSch(PtskBase):
    pass