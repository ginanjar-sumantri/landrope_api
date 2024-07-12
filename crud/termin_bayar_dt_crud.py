from fastapi_async_sqlalchemy import db
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from crud.base_crud import CRUDBase
from models import TerminBayarDt, TerminBayar, Termin
from schemas.termin_bayar_dt_sch import TerminBayarDtCreateSch, TerminBayarDtUpdateSch
from common.enum import ActivityEnum
from typing import List
from uuid import UUID


class CRUDTerminBayarDt(CRUDBase[TerminBayarDt, TerminBayarDtCreateSch, TerminBayarDtUpdateSch]):
    async def get_multi_by_termin_bayar_id(self, 
                  *, 
                  termin_bayar_id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> list[TerminBayarDt] | None:
        
        db_session = db_session or db.session
        
        query = select(TerminBayarDt).where(TerminBayarDt.termin_bayar_id == termin_bayar_id)
        
        response = await db_session.execute(query)

        return response.scalars().all()
    
    async def get_by_termin_id(self, *, termin_id: UUID, db_session: AsyncSession | None = None) -> list[TerminBayarDt] | None:
        db_session = db_session or db.session
        
        query = select(TerminBayarDt).join(TerminBayar, TerminBayar.id == TerminBayarDt.termin_bayar_id
                                    ).join(Termin, Termin.id == TerminBayar.termin_id
                                    ).where(and_(Termin.id == termin_id, TerminBayar.activity == ActivityEnum.BEBAN_BIAYA))
        
        response = await db_session.execute(query)

        return response.scalars().all()
    
    # FOR TERMIN UPDATE FUNCTION
    async def get_ids_by_termin_bayar_ids(self, 
                            *,
                            list_ids:List[UUID] | None = None,
                            db_session : AsyncSession | None = None
                            ) -> List[UUID] | None:
        
        db_session = db_session or db.session

        query = select(TerminBayarDt).where(TerminBayarDt.termin_bayar_id.in_(list_ids))

        response =  await db_session.execute(query)
        result = response.scalars().all()
        
        datas = [data.id for data in result]
        return datas


termin_bayar_dt = CRUDTerminBayarDt(TerminBayarDt)