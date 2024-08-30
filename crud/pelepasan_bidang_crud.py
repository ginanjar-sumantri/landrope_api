from fastapi import HTTPException

from crud.base_crud import CRUDBase
from models import PelepasanBidang
from schemas.pelepasan_bidang_sch import PelepasanBidangCreateSch, PelepasanBidangUpdateSch
from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from uuid import UUID
from datetime import datetime
import crud

class CRUDPelepasanBidang(CRUDBase[PelepasanBidang, PelepasanBidangCreateSch, PelepasanBidangUpdateSch]):    
    async def get_by_pelepasan_header_id(self, 
                  *, 
                  pelepasan_header_id: UUID,
                  db_session: AsyncSession | None = None
                  ) -> list[PelepasanBidang]:
        
        db_session = db_session or db.session

        response = await db_session.execute(select(PelepasanBidang).where(
            PelepasanBidang.pelepasan_header_id == pelepasan_header_id))

        return response.scalars().all()
   

pelepasan_bidang = CRUDPelepasanBidang(PelepasanBidang)