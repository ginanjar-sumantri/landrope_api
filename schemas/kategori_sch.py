from models.kategori_model import Kategori, KategoriBase, KategoriFullBase
from common.partial import optional

class KategoriCreateSch(KategoriBase):
    pass

class KategoriSch(KategoriFullBase):
    pass

@optional
class KategoriUpdateSch(KategoriBase):
    pass