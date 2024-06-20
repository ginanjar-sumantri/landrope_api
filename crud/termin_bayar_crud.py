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
    
    async def get_multi_by_termin_id(self, *, termin_id:UUID, db_session:AsyncSession | None = None) -> list[TerminBayar]:
        db_session = db_session or db.session

        query = select(TerminBayar).where(TerminBayar.termin_id == termin_id)
        response = await db_session.execute(query)
        return response.scalars().all()

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
    
    #for update in termin function
    async def get_ids_by_termin_id(self, *, termin_id:UUID | str | None = None) -> list[UUID]:
        db_session = db.session

        query = select(TerminBayar).where(TerminBayar.termin_id == termin_id)
        
        response = await db_session.execute(query)
        result = response.scalars().all()

        datas = [data.id for data in result]
        return datas


termin_bayar = CRUDTerminBayar(TerminBayar)
