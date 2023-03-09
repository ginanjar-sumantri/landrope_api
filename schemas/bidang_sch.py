from models.bidang_model import BidangBase, BidangFullBase
from common.partial import optional

class BidangCreateSch(BidangBase):
    pass

class BidangSch(BidangFullBase):
    pass

@optional
class BidangUpdateSch(BidangBase):
    pass