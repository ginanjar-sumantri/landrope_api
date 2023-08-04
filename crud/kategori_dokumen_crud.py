from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.dokumen_model import KategoriDokumen
from schemas.kategori_dokumen_sch import KategoriDokumenCreateSch, KategoriDokumenUpdateSch
from typing import List
from uuid import UUID

class CRUDKategoriDokumen(CRUDBase[KategoriDokumen, KategoriDokumenCreateSch, KategoriDokumenUpdateSch]):
    pass

kategori_dokumen = CRUDKategoriDokumen(KategoriDokumen)