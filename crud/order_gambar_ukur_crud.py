from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from crud.base_crud import CRUDBase
from models.order_gambar_ukur_model import OrderGambarUkur, OrderGambarUkurBidang, OrderGambarUkurTembusan
from schemas.order_gambar_ukur_sch import OrderGambarUkurCreateSch, OrderGambarUkurUpdateSch
from uuid import UUID
from datetime import datetime



class CRUDOrderGambarUkur(CRUDBase[OrderGambarUkur, OrderGambarUkurCreateSch, OrderGambarUkurUpdateSch]):
    async def create_order_gambar_ukur(
            self, 
            *, 
            obj_in: OrderGambarUkurCreateSch, 
            created_by_id : UUID | str | None = None, 
            db_session : AsyncSession | None = None) -> OrderGambarUkur :
        db_session = db_session or db.session
        db_obj = self.model.from_orm(obj_in) #type ignore
        db_obj.created_at = datetime.utcnow()
        db_obj.updated_at = datetime.utcnow()
        if created_by_id:
            db_obj.created_by_id = created_by_id

        try:
            
            for i in obj_in.bidangs:
                bidang = OrderGambarUkurBidang(bidang_id=i,
                                               created_by_id=created_by_id,
                                               updated_by_id=created_by_id)
                
                db_obj.bidangs.append(bidang)
            
            for t in obj_in.tembusans:
                tembusan = OrderGambarUkurTembusan(tembusan_id=t,
                                                  created_by_id=created_by_id,
                                                  updated_by_id=created_by_id)
                db_obj.tembusans.append(tembusan)

            db_session.add(db_obj)
            await db_session.commit()
        except exc.IntegrityError:
            await db_session.rollback()
            raise HTTPException(status_code=409, detail="Resource already exists")
        
        await db_session.refresh(db_obj)
        return db_obj

order_gambar_ukur = CRUDOrderGambarUkur(OrderGambarUkur)