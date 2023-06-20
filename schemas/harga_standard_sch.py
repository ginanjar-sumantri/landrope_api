from models.master_model import HargaStandard, HargaStandardBase
from common.partial import optional

class HargaStandardCreateSch(HargaStandardBase):
    pass

class HargaStandardSch(HargaStandard):
    pass

@optional
class HargaStandardUpdateSch(HargaStandardBase):
    pass