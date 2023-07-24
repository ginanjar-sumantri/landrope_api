from fastapi_async_sqlalchemy import db
from sqlmodel import select, func, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base_crud import CRUDBase
from models.master_model import JenisSurat
from schemas.jenis_surat_sch import JenisSuratCreateSch, JenisSuratUpdateSch
from common.enum import JenisAlashakEnum

class CRUDJenisSurat(CRUDBase[JenisSurat, JenisSuratCreateSch, JenisSuratUpdateSch]):
    async def get_by_jenis_alashak_and_name(self, *, jenis_alashak: str, name:str, db_session: AsyncSession | None = None) -> JenisSurat | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(
            func.lower(func.trim(func.replace(self.model.name, ' ', ''))) == name.strip().lower().replace(' ', ''),
            func.lower(func.trim(func.replace(self.model.jenis_alashak, ' ', ''))) == jenis_alashak.strip().lower().replace(' ', '')))
        
        response = await db_session.execute(query)

        return response.scalar_one_or_none()

jenissurat = CRUDJenisSurat(JenisSurat)