from models.bidang_model import BidangoverlapBase, BidangoverlapFullBase, BidangoverlapRawBase
from common.partial import optional
from common.as_form import as_form

@as_form
class BidangoverlapCreateSch(BidangoverlapBase):
    pass

class BidangoverlapRawSch(BidangoverlapRawBase):
    pass

class BidangoverlapSch(BidangoverlapFullBase):
    pass

@as_form
@optional
class BidangoverlapUpdateSch(BidangoverlapBase):
    pass