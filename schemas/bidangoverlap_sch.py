from models.bidang_model import BidangoverlapBase, BidangoverlapFullBase, BidangoverlapRawBase
from common.partial import optional

class BidangoverlapCreateSch(BidangoverlapBase):
    pass

class BidangoverlapRawSch(BidangoverlapRawBase):
    pass

class BidangoverlapSch(BidangoverlapFullBase):
    pass

@optional
class BidangoverlapUpdateSch(BidangoverlapBase):
    pass