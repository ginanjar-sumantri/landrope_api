from models.bidang_model import BidangoverlapBase, BidangoverlapFullBase
from common.partial import optional

class BidangoverlapCreateSch(BidangoverlapBase):
    pass

class BidangoverlapSch(BidangoverlapFullBase):
    pass

@optional
class BidangoverlapUpdateSch(BidangoverlapBase):
    pass