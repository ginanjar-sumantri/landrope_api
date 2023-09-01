from models.giro_model import GiroBase, GiroFullBase
from common.partial import optional


class GiroCreateSch(GiroBase):
    pass

class GiroSch(GiroFullBase):
    pass

@optional
class GiroUpdateSch(GiroFullBase):
    pass