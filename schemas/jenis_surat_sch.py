from models.master_model import JenisSuratBase, JenisSurat
from common.partial import optional

class JenisSuratCreateSch(JenisSuratBase):
    pass

class JenisSuratSch(JenisSurat):
    pass

@optional
class JenisSuratUpdateSch(JenisSuratBase):
    pass