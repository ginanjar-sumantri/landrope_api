from crud.base_crud import CRUDBase
from models.kategori_model import KategoriProyek
from schemas.kategori_proyek_sch import KategoriProyekCreateSch, KategoriProyekUpdateSch


class CRUDKategoriProyek(CRUDBase[KategoriProyek, KategoriProyekCreateSch, KategoriProyekUpdateSch]):
    pass

kategori_proyek = CRUDKategoriProyek(KategoriProyek)