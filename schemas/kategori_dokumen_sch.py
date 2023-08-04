from models.dokumen_model import KategoriDokumen, KategoriDokumenBase, KategoriDokumenFullBase
from common.partial import optional
from common.as_form import as_form
from sqlmodel import SQLModel, Field
from datetime import date, datetime

class KategoriDokumenCreateSch(KategoriDokumenBase):
    pass

class KategoriDokumenSch(KategoriDokumenFullBase):
    pass

@optional
class KategoriDokumenUpdateSch(KategoriDokumenBase):
    pass