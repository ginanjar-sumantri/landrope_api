from models.kategori_model import KategoriProyek, KategoriProyekBase, KategoriProyekFullBase
from common.partial import optional

class KategoriProyekCreateSch(KategoriProyekBase):
    pass

class KategoriProyekSch(KategoriProyekFullBase):
    pass

@optional
class KategoriProyekUpdateSch(KategoriProyekBase):
    pass