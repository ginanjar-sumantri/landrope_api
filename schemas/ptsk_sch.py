from models.ptsk_model import PtskBase, PtskFullBase
from common.partial import optional

class PTSKCreateSch(PtskBase):
    pass

class PTSKSch(PtskFullBase):
    pass

@optional
class PTSKUpdateSch(PtskBase):
    pass