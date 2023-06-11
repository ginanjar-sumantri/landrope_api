from models.kjb_model import KjbDt, KjbDtBase, KjbDtFullBase
from common.partial import optional

class KjbDtCreateSch(KjbDtBase):
    pass

class KjbDtSch(KjbDtFullBase):
    pass

@optional
class KjbDtUpdateSch(KjbDtBase):
    pass