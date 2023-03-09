from models.ptsk_model import PTSKBase, PTSKFullBase
from common.partial import optional

class PTSKCreateSch(PTSKBase):
    pass

class PTSKSch(PTSKFullBase):
    pass

@optional
class PTSKUpdateSch(PTSKBase):
    pass