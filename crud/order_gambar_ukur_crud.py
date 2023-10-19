from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from fastapi_async_sqlalchemy import db
from crud.base_crud import CRUDBase
from models import OrderGambarUkur, OrderGambarUkurBidang, OrderGambarUkurTembusan, KjbDt, HasilPetaLokasi, Bidang, Skpt, KjbHd
from schemas.order_gambar_ukur_sch import OrderGambarUkurCreateSch, OrderGambarUkurUpdateSch
from uuid import UUID
from datetime import datetime



class CRUDOrderGambarUkur(CRUDBase[OrderGambarUkur, OrderGambarUkurCreateSch, OrderGambarUkurUpdateSch]):
    async def get_by_id(self, 
                  *, 
                  id: UUID | str | None = None,
                  db_session: AsyncSession | None = None
                  ) -> OrderGambarUkur | None:
        
        db_session = db_session or db.session
        
        query = select(OrderGambarUkur).where(OrderGambarUkur.id == id
                                                ).options(selectinload(OrderGambarUkur.notaris_tujuan)
                                                ).options(selectinload(OrderGambarUkur.bidangs
                                                                        ).options(selectinload(OrderGambarUkurBidang.kjb_dt
                                                                                            ).options(selectinload(KjbDt.hasil_peta_lokasi
                                                                                                                ).options(selectinload(HasilPetaLokasi.bidang
                                                                                                                                    ).options(selectinload(Bidang.hasil_peta_lokasi)
                                                                                                                                    ).options(selectinload(Bidang.skpt
                                                                                                                                                           ).options(selectinload(Skpt.ptsk))
                                                                                                                                    ).options(selectinload(Bidang.jenis_surat)
                                                                                                                                    ).options(selectinload(Bidang.pemilik)
                                                                                                                                    )
                                                                                                                ).options(selectinload(HasilPetaLokasi.pemilik)
                                                                                                                )
                                                                                            ).options(selectinload(KjbDt.jenis_surat)
                                                                                            ).options(selectinload(KjbDt.kjb_hd
                                                                                                                    ).options(selectinload(KjbHd.sales))
                                                                                            )
                                                                        )
                                                ).options(selectinload(OrderGambarUkur.tembusans))
                                                   
                                                    

        response = await db_session.execute(query)

        return response.scalar_one_or_none()
    
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