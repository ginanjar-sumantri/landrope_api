import random
import string

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from fastapi.security import HTTPBearer
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from crud.base_crud import CRUDBase
from models import Role, PeminjamanHeader
from schemas.peminjaman_header_sch import PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch
from typing import List
from sqlalchemy import text
from fastapi_async_sqlalchemy import db



from typing import Optional


token_auth_scheme = HTTPBearer()


class CRUDPeminjamanHeader(CRUDBase[PeminjamanHeader, PeminjamanHeaderCreateSch, PeminjamanHeaderUpdateSch]):
    async def get_by_id_bidang(
        self,
        *,
        id: str,
        db_session: AsyncSession | None = None,
    ) -> PeminjamanHeader | None:
        db_session = db_session or super().get_db().session

        query = select(PeminjamanHeader).where(PeminjamanHeader.bidang_id == id)

        response = await db_session.execute(query)
            
        return response.scalar_one_or_none()
    
peminjaman_header = CRUDPeminjamanHeader(PeminjamanHeader)
