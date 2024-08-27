import random
import string

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from fastapi.security import HTTPBearer
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import Role, PeminjamanBidang
from schemas.peminjaman_bidang_sch import PeminjamanBidangCreateSch, PeminjamanBidangUpdateSch
from typing import List
from sqlalchemy import text
from fastapi_async_sqlalchemy import db



from typing import Optional


token_auth_scheme = HTTPBearer()


class CRUDPeminjamanBidang(CRUDBase[PeminjamanBidang, PeminjamanBidangCreateSch, PeminjamanBidangUpdateSch]):
    async def get_by_id_bidang(
        self,
        *,
        id: str,
        db_session: AsyncSession | None = None,
    ) -> PeminjamanBidang | None:
        db_session = db_session or super().get_db().session

        query = select(PeminjamanBidang).where(PeminjamanBidang.bidang_id == id)

        response = await db_session.execute(query)
            
        return response.scalar_one_or_none()
    
peminjaman_bidang = CRUDPeminjamanBidang(PeminjamanBidang)
