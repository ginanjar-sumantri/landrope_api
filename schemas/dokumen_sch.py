from models.dokumen_model import Dokumen, DokumenBase, DokumenFullBase
from common.partial import optional

class DokumenCreateSch(DokumenBase):
    pass

class DokumenSch(DokumenFullBase):
    pass

@optional
class DokumenUpdateSch(DokumenBase):
    pass