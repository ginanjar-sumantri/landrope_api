import random
import string

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from fastapi.security import HTTPBearer
from sqlmodel import and_, select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import Role, PeminjamanBidang, Bidang
from schemas.peminjaman_bidang_sch import PeminjamanBidangCreateSch, PeminjamanBidangUpdateSch
from typing import List
from sqlalchemy import text
from fastapi_async_sqlalchemy import db
from uuid import UUID


token_auth_scheme = HTTPBearer()


class CRUDPeminjamanBidang(CRUDBase[PeminjamanBidang, PeminjamanBidangCreateSch, PeminjamanBidangUpdateSch]):
    async def get_by_id_bidang_dan_alashak(
        self,
        *,
        search: UUID | str,
        db_session: AsyncSession | None = None,
    ) -> PeminjamanBidang | None:
                
        db_session = db_session or db.session

        query = (select(PeminjamanBidang)
        .join(PeminjamanBidang.bidang)
        .where(
            or_(
                PeminjamanBidang.bidang_id == search if isinstance(search, UUID) else None,
                Bidang.alashak == search if isinstance(search, str) else None
            )
        )
    )

        response = await db_session.execute(query)
            
        return response.scalar_one_or_none()
    
peminjaman_bidang = CRUDPeminjamanBidang(PeminjamanBidang)
