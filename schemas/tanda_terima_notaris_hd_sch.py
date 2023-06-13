from models.tanda_terima_notaris_model import TandaTerimaNotarisHd, TandaTerimaNotarisHdBase, TandaTerimaNotarisHdFullBase
from common.partial import optional

class TandaTerimaNotarisHdCreateSch(TandaTerimaNotarisHdBase):
    pass

class TandaTerimaNotarisHdSch(TandaTerimaNotarisHdFullBase):
    pass

@optional
class TandaTerimaNotarisHdUpdateSch(TandaTerimaNotarisHdBase):
    pass