from models.notaris_model import NotarisBase, NotarisFullBase
from common.partial import optional

class NotarisCreateSch(NotarisBase):
    pass

class NotarisSch(NotarisFullBase):
    pass

@optional
class NotarisUpdateSch(NotarisBase):
    pass