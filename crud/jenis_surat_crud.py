from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.master_model import JenisSurat
from schemas.jenis_surat_sch import JenisSuratCreateSch, JenisSuratUpdateSch

class CRUDJenisSurat(CRUDBase[JenisSurat, JenisSuratCreateSch, JenisSuratUpdateSch]):
    pass

jenissurat = CRUDJenisSurat(JenisSurat)