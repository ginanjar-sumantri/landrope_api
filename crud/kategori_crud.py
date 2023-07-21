from crud.base_crud import CRUDBase
from models.kategori_model import Kategori
from schemas.kategori_sch import KategoriCreateSch, KategoriUpdateSch


class CRUDKategori(CRUDBase[Kategori, KategoriCreateSch, KategoriUpdateSch]):
    pass

kategori = CRUDKategori(Kategori)