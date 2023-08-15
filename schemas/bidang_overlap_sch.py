from models.bidang_overlap_model import BidangOverlap, BidangOverlapBase, BidangOverlapFullBase, BidangOverlapRawBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import Field

@as_form
class BidangOverlapCreateSch(BidangOverlapBase):
    pass

class BidangOverlapRawSch(BidangOverlapRawBase):
    pass

class BidangOverlapSch(BidangOverlapFullBase):
    pass

@as_form
@optional
class BidangOverlapUpdateSch(BidangOverlapBase):
    pass