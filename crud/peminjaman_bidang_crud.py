import random
import string

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from fastapi.security import HTTPBearer
from sqlmodel import and_, select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import Role, PeminjamanBidang
from schemas.peminjaman_bidang_sch import PeminjamanBidangCreateSch, PeminjamanBidangUpdateSch
from typing import List
from sqlalchemy import text
from fastapi_async_sqlalchemy import db
from uuid import UUID


token_auth_scheme = HTTPBearer()


class CRUDPeminjamanBidang(CRUDBase[PeminjamanBidang, PeminjamanBidangCreateSch, PeminjamanBidangUpdateSch]):
    async def get_by_peminjaman_header_id(self, 
                  *, 
                  peminjaman_header_id: UUID,
                  db_session: AsyncSession | None = None
                  ) -> list[PeminjamanBidang]:
        
        db_session = db_session or db.session

        response = await db_session.execute(select(PeminjamanBidang).where(
            PeminjamanBidang.peminjaman_header_id == peminjaman_header_id))

        return response.scalars().all()
    
peminjaman_bidang = CRUDPeminjamanBidang(PeminjamanBidang)
