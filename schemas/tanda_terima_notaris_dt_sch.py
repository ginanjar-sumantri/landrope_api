from models.tanda_terima_notaris_model import TandaTerimaNotarisDt, TandaTerimaNotarisDtBase, TandaTerimaNotarisDtFullBase
from common.partial import optional

class TandaTerimaNotarisDtCreateSch(TandaTerimaNotarisDtBase):
    pass

class TandaTerimaNotarisDtSch(TandaTerimaNotarisDtFullBase):
    pass

@optional
class TandaTerimaNotarisDtUpdateSch(TandaTerimaNotarisDtBase):
    pass