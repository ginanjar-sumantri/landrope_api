from fastapi_async_sqlalchemy import db
from fastapi_pagination import Params, Page
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlmodel.sql.expression import Select

from common.ordered import OrderEnumSch
from crud.base_crud import CRUDBase
from models.master_model import BebanBiaya
from schemas.beban_biaya_sch import BebanBiayaSch, BebanBiayaCreateSch, BebanBiayaUpdateSch, BebanBiayaGroupingSch
from typing import List
from uuid import UUID

class CRUDBebanBiaya(CRUDBase[BebanBiaya, BebanBiayaCreateSch, BebanBiayaUpdateSch]):
    async def get_beban_biaya_add_pay(self, *,
                    list_id:list[UUID]|None = [],
                    db_session : AsyncSession | None = None
                    ) -> List[BebanBiaya] | None:
        
        db_session = db_session or db.session
        
        query = select(self.model).where(and_(BebanBiaya.id.in_(list_id), BebanBiaya.is_add_pay == True))

        response =  await db_session.execute(query)
        return response.scalars().all()
    
    async def get_multi_grouping_beban_biaya_by_termin_id(self, *,
                    termin_id:UUID,
                    db_session : AsyncSession | None = None
                    ) -> List[BebanBiayaGroupingSch] | None:
        
        db_session = db_session or db.session
        
        query = f"""select 
                beban_biaya.id, 
                beban_biaya.name, 
                sum(invoice_detail.amount) as amount,
                termin.code as memo_code,
                termin.nomor_memo as nomor_memo,
                termin.id as termin_id
            from 
                beban_biaya 
            inner join 
                bidang_komponen_biaya on beban_biaya.id = bidang_komponen_biaya.beban_biaya_id
            inner join 
                invoice_detail on bidang_komponen_biaya.id = invoice_detail.bidang_komponen_biaya_id
            inner join 
                invoice on invoice.id = invoice_detail.invoice_id
            inner join 
                termin on termin.id = invoice.termin_id
            where 
                termin.id = '{termin_id}'
                and bidang_komponen_biaya.is_void != True
                and bidang_komponen_biaya.beban_pembeli = True
                and invoice.is_void != True
            Group By 
                termin.id, beban_biaya.id
            Order By 
                beban_biaya.id"""
    
        response =  await db_session.execute(query)
        rows = response.fetchall()
    
        result = [BebanBiayaGroupingSch(beban_biaya_id=row[0],
                                            beban_biaya_name=row[1],
                                            amount=row[2],
                                            memo_code=row[3],
                                            nomor_memo=row[4],
                                            termin_id=row[5]) for row in rows]

        return result

bebanbiaya = CRUDBebanBiaya(BebanBiaya)