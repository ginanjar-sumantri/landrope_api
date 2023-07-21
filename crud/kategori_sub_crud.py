from crud.base_crud import CRUDBase
from models.kategori_model import KategoriSub
from schemas.kategori_sub_sch import KategoriSubCreateSch, KategoriSubUpdateSch


class CRUDKategoriSub(CRUDBase[KategoriSub, KategoriSubCreateSch, KategoriSubUpdateSch]):
    pass

kategori_sub = CRUDKategoriSub(KategoriSub)