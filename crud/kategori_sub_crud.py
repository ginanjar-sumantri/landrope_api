from fastapi_async_sqlalchemy import db
from sqlmodel import func, select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models.kategori_model import KategoriSub
from schemas.kategori_sub_sch import KategoriSubCreateSch, KategoriSubUpdateSch
from uuid import UUID


class CRUDKategoriSub(CRUDBase[KategoriSub, KategoriSubCreateSch, KategoriSubUpdateSch]):
    async def get_by_name_and_kategori_id(
        self, *, name: str, kategori_id:UUID, db_session: AsyncSession | None = None
    ) -> KategoriSub:
        db_session = db_session or db.session
        query = select(self.model).where(func.lower(func.trim(func.replace(self.model.name, ' ', ''))) == name.strip().lower().replace(' ', ''))
        query = query.filter(KategoriSub.kategori_id == kategori_id)
        
        obj = await db_session.execute(query)
        return obj.scalar_one_or_none()


kategori_sub = CRUDKategoriSub(KategoriSub)