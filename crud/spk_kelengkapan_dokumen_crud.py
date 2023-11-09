from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models.spk_model import SpkKelengkapanDokumen
from schemas.spk_kelengkapan_dokumen_sch import SpkKelengkapanDokumenCreateSch, SpkKelengkapanDokumenUpdateSch
from uuid import UUID
from typing import List

class CRUDSpkKelengkapanDokumen(CRUDBase[SpkKelengkapanDokumen, SpkKelengkapanDokumenCreateSch, SpkKelengkapanDokumenUpdateSch]):
    async def get_multi_not_in_id_removed(self, *, spk_id:UUID, list_ids: List[UUID | str], db_session : AsyncSession | None = None) -> List[SpkKelengkapanDokumen] | None:
        db_session = db_session or db.session
        query = select(self.model).where(and_(~self.model.id.in_(list_ids), self.model.spk_id == spk_id))
        response =  await db_session.execute(query)
        return response.scalars().all()

spk_kelengkapan_dokumen = CRUDSpkKelengkapanDokumen(SpkKelengkapanDokumen)