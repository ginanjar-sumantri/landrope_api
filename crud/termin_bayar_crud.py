from fastapi_async_sqlalchemy import db
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import TerminBayar
from schemas.termin_bayar_sch import TerminBayarCreateSch, TerminBayarUpdateSch, TerminBayarSch, TerminBayarForPrintout
from typing import List
from uuid import UUID


class CRUDTerminBayar(CRUDBase[TerminBayar, TerminBayarCreateSch, TerminBayarUpdateSch]):
    async def get_multi_by_termin_id_for_printout(self, 
                        *,
                        termin_id:UUID,
                        db_session : AsyncSession | None = None
                        ) -> List[TerminBayarForPrintout]:
        db_session = db_session or db.session
    
        query = select(TerminBayar)
        query = query.filter(TerminBayar.termin_id == termin_id)
        query = query.options(selectinload(TerminBayar.rekening))

        response =  await db_session.execute(query)
        return response.scalars().all()


termin_bayar = CRUDTerminBayar(TerminBayar)
