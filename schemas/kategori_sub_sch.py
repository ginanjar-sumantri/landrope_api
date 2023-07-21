from models.kategori_model import KategoriSub, KategoriSubBase, KategoriSubFullBase
from common.partial import optional

class KategoriSubCreateSch(KategoriSubBase):
    pass

class KategoriSubSch(KategoriSubFullBase):
    pass

@optional
class KategoriSubUpdateSch(KategoriSubBase):
    pass